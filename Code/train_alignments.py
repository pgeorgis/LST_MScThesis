import os, glob, re, itertools
from collections import defaultdict
from matplotlib import pyplot as plt
import seaborn as sns
sns.set(font_scale=1.0)
from auxiliary_functions import *
from pathlib import Path
local_dir = Path(str(os.getcwd()))
parent_dir = local_dir.parent
from phonetic_distance import *
os.chdir(local_dir)

def correct_tr(tr):
    tr = re.sub('g', 'ɡ', tr)
    tr = re.sub('ʅ', 'ɻ̩', tr)
    tr = re.sub('ł', 'ɫ', tr) #probably meant to be dark l
    tr = re.sub('ȵ', 'ɲ', tr)
    tr = re.sub('ɿ', 'ɹ̩', tr)
    tr = re.sub('t͡s', 'ʦ', tr)
    tr = re.sub('ᴀ', 'ä', tr)
    tr = re.sub('ᴇ', 'ɛ', tr)
    tr = re.sub('ǝ', 'ə', tr)
    tr = re.sub('ı', 'ɪ', tr) #most likely equivalent I can find
    tr = re.sub('ˁ', 'ˤ', tr)
    tr = re.sub('̣', '̤', tr)
    tr = re.sub('_', '-', tr)
    return tr

class MultipleAlignFile:
    def __init__(self, filepath, gap_ch='-'):
        self.filepath = filepath
        self.gap_ch = gap_ch
        self.group = ''
        self.gloss = ''
        self.varieties = []
        self.segments = {}
        self.pairwise = {}
        self.load_alignments()
        self.generate_pairwise()
        self.unknown_ch = set(ch for variety in self.segments 
                              for seg in self.segments[variety] 
                              for ch in seg 
                              if ch not in all_sounds+diacritics+['-'])
    
    def load_alignments(self):
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
            self.group = lines[0].strip()
            self.gloss = lines[1].strip()
            alignments = lines[2:]
            #if alignments[-1].split('.')[0] == 'LOCAL':
            #   alignments = lines[2:-1]
            
            for i in range(len(alignments)):
                line = alignments[i]
                if alignments[i].split('.')[0] in ['LOCAL', 'SWAPS']:
                    break
                line = line.strip()
                if '.' in line:
                    variety = line.split('.')[0]
                else:
                    variety = line.split('\t')[0]
                segments = correct_tr(line).split('\t')[1:]
                self.segments[variety] = segments
            
            self.varieties.extend(list(self.segments.keys()))
    
    def generate_pairwise(self):
        for i in range(len(self.varieties)):
            for j in range(i+1, len(self.varieties)):
                variety1, variety2 = self.varieties[i], self.varieties[j]
                segs1 = self.segments[variety1]
                segs2 = self.segments[variety2]
                alignment = list(zip(segs1, segs2))
                alignment = [pair for pair in alignment if pair != (self.gap_ch, self.gap_ch)]
                self.pairwise[(variety1, variety2)] = alignment


#Designate directories where gold alignments are stored
alignment_dir = str(parent_dir) + '/Datasets/Alignments'
pairwise_dir = alignment_dir + '/psa'
multiple_dir = alignment_dir + '/msa'

#Load pairwise alignments
#os.chdir(pairwise_dir)
#pairwise_files = glob.glob('*.psa')
#os.chdir(local_dir)

#Load multiple alignments
os.chdir(multiple_dir)
print('Loading alignments...')
multiple_alignments = [MultipleAlignFile(path) for path in glob.glob('*.msa')]
os.chdir(local_dir)

#Separate alignments into datasets by grouping
#Andean, Bai, Bulgarian, Dutch, French, Germanic, Japanese, 
#Norwegian, Ob-Ugrian, Romance, Sinitic, Slavic
alignment_datasets = defaultdict(lambda:[])
for alignment in multiple_alignments:
    alignment_datasets[format_as_variable(alignment.group)].append(alignment)
globals().update(alignment_datasets)

test_datasets = [Andean, Bai, French, Germanic, Japanese, Ob_Ugrian, Romance, Sinitic, Slavic]
#not including: Bulgarian/Norwegian/Dutch (too big)

#%%
def test_alignments(dataset, 
                    align_func=phone_align,
                    gap_ch='-',
                    print_progress=True,
                    **kwargs):
    correct = defaultdict(lambda:[])
    incorrect = defaultdict(lambda:[])
    for align_set in dataset:
        n_correct = 0
        n_incorrect = 0
        for variety_pair in align_set.pairwise:
            gold_alignment = align_set.pairwise[variety_pair]
            segs1 = [pair[0] for pair in gold_alignment if pair[0] != gap_ch]
            segs2 = [pair[1] for pair in gold_alignment if pair[1] != gap_ch]
            try:
                auto_alignment = align_func(segs1, segs2, **kwargs)
            except IndexError:
                print(variety_pair, gold_alignment)
                raise KeyError
                
            #need to standardize order because they might yield same alignment but
            #with gap sequences reordered e.g.
            #[('-', 'ʃ'), ('o', '-')] vs. [('o', '-'), ('-', 'ʃ')]
            if sorted(auto_alignment) == sorted(gold_alignment):
                correct[variety_pair].append((''.join(segs1), ''.join(segs2), gold_alignment))
                n_correct += 1
            else:
                incorrect[variety_pair].append((''.join(segs1), ''.join(segs2), gold_alignment, auto_alignment))
                n_incorrect += 1
        if print_progress == True:
            print(f'{align_set.gloss}\n\tAccuracy: {round(n_correct/(n_correct+n_incorrect), 2)}')
    
    total_correct = sum(len(correct[pair]) for pair in correct)
    total_incorrect = sum(len(incorrect[pair]) for pair in incorrect)
    total = total_correct + total_incorrect
    accuracy = total_correct/total
    return accuracy, correct, incorrect


def test_parameters(datasets=test_datasets, 
                    align_func=[phone_align],
                    gop=[-0.5],
                    **kwargs):
    parameter_combinations = list(itertools.product(align_func, gop))
    
    results = defaultdict(lambda:defaultdict(lambda:{}))
    for dataset in datasets:
        group = dataset[0].group
        print(f'TESTING DATASET: {group.upper()}')
        for align_func, gop in parameter_combinations:
            accuracy, correct, incorrect = test_alignments(dataset=dataset, 
                                                           align_func=align_func, 
                                                           gop=gop, 
                                                           segmented=True,
                                                           print_progress=False,
                                                           **kwargs)
            results[(align_func, gop)][group] = (accuracy, correct, incorrect)
            print(f'{gop}: {round(accuracy, 2)}')
        print('\n')
    
    #Get total accuracy if there is more than one dataset
    if len(datasets) > 1:
        for parameter_set in results:
            results[parameter_set]['Total'] = [0, 0, 0]
            for dataset in results[parameter_set]:
                if dataset != 'Total':
                    correct = sum([len(results[parameter_set][dataset][1][pair]) 
                                   for pair in results[parameter_set][dataset][1]])
                    
                    incorrect = sum([len(results[parameter_set][dataset][2][pair]) 
                                   for pair in results[parameter_set][dataset][2]])
                
                results[parameter_set]['Total'][1] += correct
                results[parameter_set]['Total'][2] += incorrect
            total_correct = results[parameter_set]['Total'][1]
            total_incorrect = results[parameter_set]['Total'][2]
            total_accuracy = total_correct / (total_correct + total_incorrect)
            results[parameter_set]['Total'][0] = total_accuracy
            results[parameter_set]['Average'] = [mean([results[parameter_set][dataset][0] for dataset in results[parameter_set]]),
                                                 None,None]
                
    
    return results
        


def plot_results(results, parameter_index, plt_title=None):
    parameters = [item[parameter_index] for item in results.keys()]
    datasets = list(results[list(results.keys())[0]].keys())
    for dataset in datasets:
        values = [results[p][dataset][0] for p in results]
        plt.plot(parameters, values, label=dataset)
    plt.legend(loc='best', prop={'size': 6})
    plt.ylabel('Accuracy')
    plt.xlabel('Parameter Value')
    if plt_title != None:
        plt.title(plt_title)
        plt.savefig(f'{alignment_dir}/{plt_title}.png', dpi=200)
    plt.show()
    plt.close()


def write_results(results, parameter_index, output_file, sep=','):
    with open(output_file, 'w') as f:
        f.write(sep.join(['Parameter_Value','Group','Accuracy']))
        f.write('\n')
        for parameters in results:
            parameter = parameters[parameter_index]
            for group in results[parameters]:
                accuracy, correct, incorrect = results[parameters][group]
                f.write(sep.join([str(parameter),group,str(accuracy)]))
                f.write('\n')

    
#%%
#EXTRACT GOLD SEGMENT ALIGNMENT PROBABILITIES
def extract_correspondences():
    print('Extracting gold correspondences...')
    correspondences = defaultdict(lambda:defaultdict(lambda:0))
    #correspondence_examples = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:[])))
    for align_set in multiple_alignments:
        for variety_pair in align_set.pairwise:
            alignment = align_set.pairwise[variety_pair]
            for pair in alignment:
                seg1, seg2 = pair
                #correspondence_examples[pair][align_set.group][variety_pair].append(alignment)
                #seg1 = strip_diacritics(seg1, excepted=inter_diacritics+['⁰', '¹', '²', '³', '⁴', '⁵'])
                #seg2 = strip_diacritics(seg2, excepted=inter_diacritics+['⁰', '¹', '²', '³', '⁴', '⁵'])
                #if (seg1, seg2) != pair:
                #    correspondence_examples[(seg1, seg2)][align_set.group][variety_pair].append(alignment)
                if seg1 != seg2: #exclude identical segment pairs
                    if ((len(seg1) > 0) and (len(seg2) > 0)):
                        correspondences[seg1][seg2] += 1
                        correspondences[seg2][seg1] += 1
    correspondence_probs = {}
    for seg1 in correspondences:
        correspondence_probs[seg1] = normalize_dict(correspondences[seg1])
    return correspondences 

#%%
missing_phone_ids = []
def write_correspondences(output_file=alignment_dir + '/correspondences.csv'):
    with open(output_file, 'w') as f:
        phon_features = sorted(list(features))
        f.write(','.join(['segment1','segment2','count','prob']+phon_features))
        f.write('\n')
        for seg1 in correspondences:
            if seg1 != '-':
                try:
                    seg1_id = phone_id(seg1)
                except KeyError:
                    missing_phone_ids.append(seg1)
                    continue
            else:
                seg1_id = {feature:0 for feature in phon_features}
            for seg2 in correspondences[seg1]:
                if seg2 != '-':
                    try:
                        seg2_id = phone_id(seg2)
                    except KeyError:
                        missing_phone_ids.append(seg2)
                        continue
                else:
                    seg2_id = {feature:0 for feature in phon_features}
                count = correspondences[seg1][seg2]
                prob = correspondence_probs[seg1][seg2]
                feature_matches = ['1' if seg1_id[feature] == seg2_id[feature] else '0' for feature in phon_features]
                f.write(','.join([seg1, seg2, str(count), str(prob)]+feature_matches))
                f.write('\n')

def lookup_correspondence(seg1, seg2, strip_dia=True):
    matches = defaultdict(lambda:defaultdict(lambda:[]))
    for align_set in multiple_alignments:
        for variety_pair in align_set.pairwise:
            alignment = align_set.pairwise[variety_pair]
            if strip_dia == True:
                alignment = [(strip_diacritics(pair[0]), strip_diacritics(pair[1]))
                             for pair in alignment]
            if (seg1, seg2) in alignment:
                matches[align_set.group][variety_pair].append(alignment)
            elif (seg2, seg1) in alignment:
                matches[align_set.group][variety_pair].append(alignment)
    return matches
            
        
            
    
    
    