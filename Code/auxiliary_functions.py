from collections import defaultdict
import pandas as pd

def strip_ch(string, to_remove):
    """Removes a set of characters from strings"""
    return ''.join([ch for ch in string if ch not in to_remove])

def csv_to_dict(csvfile, header=True, sep=',', start=0, encoding='utf_8'):
    """Reads a CSV file into a dictionary"""
    csv_dict = defaultdict(lambda:defaultdict(lambda:''))
    with open(csvfile, 'r', encoding=encoding) as csv_file:
        csv_file = csv_file.readlines()
        columns = [item.strip() for item in csv_file[start].split(sep)]
        if header == True:
            start += 1
        for i in range(start, len(csv_file)):
            line = [item.strip() for item in csv_file[i].split(sep)]
            for j in range(len(columns)):
                key = ''
                if header == True:
                    key += columns[j]
                else:
                    key += str(j)
                try:
                    csv_dict[i][key] = line[j]
                except IndexError:
                    pass
    return csv_dict

def xlsx_to_csv(excel_path, csv_path=None, sheet=None, 
                sep=',', index=None, header=True):
    """Converts an Excel file to a CSV file"""
    if sheet != None:
        excel_file = pd.read_excel(excel_path, sheet_name=sheet)
    else:
        excel_file = pd.read_excel(excel_path)
    
    #Automatically name the output .csv file the same as the Excel file if 
    #no other name is specified
    if csv_path == None:
        csv_path = excel_path.split('.')[0] + '.csv'
    
    #Write to .csv file
    excel_file.to_csv(csv_path, index=index, header=header, sep=sep)
    print(f'Wrote file to {csv_path}.')
    
    
    


def normalize_dict(dict_, default=False, lmbda=None, return_=True):
    """Normalizes the values of a dictionary"""
    """If default==True, returns a default dictionary with default value lmbda"""
    """If return_==False, modifies the input dictionary without returning anything"""
    if default==True:
        normalized = defaultdict(lambda:lmbda)
    else:
        normalized = {}
    total = sum(list(dict_.values()))
    for key in dict_:
        if return_ == True:
            normalized[key] = dict_[key] / total
        else:
            dict_[key] = dict_[key] / total
    if return_ == True:
        return normalized