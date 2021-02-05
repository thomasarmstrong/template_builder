from template_builder.fit_templates import TemplateFitter
from os import listdir
import multiprocessing
import gzip
import pickle

def get_file_list(directories):
    files_before_simulation = []
    for path in directories:
        for file in listdir(path):
            files_before_simulation.append(path+file)
    return files_before_simulation

output_paths = ['/scratch3/armstrong/LST/d2020-02-12/Data/sim_hessarray/LST/0.0deg/Data/']
files_after = get_file_list(output_paths)
# fitter = TemplateFitter(min_fit_pixels=2000, bounds=((-5, 1), (-1.5, 1.5)))
# fitter.generate_templates(files_after, 'test.templates.gz', max_events=50000)

fitter = TemplateFitter(min_fit_pixels=2000, verbose=True)
pool = multiprocessing.Pool(4)

templates = dict()
variance_templates = dict()

tasks = []
count = 0
for n, i in enumerate(files_after):
    tasks.append([i, '/scratch3/armstrong/LST/d2020-02-12/Data/temp_%s.templates.gz' % n])
    count+=1
    if count > 3:
        break
pool.starmap(fitter.pool_generate_templates, tasks)

out_dict = {}
count = 0
for n, i in enumerate(files_after):
    file_list = gzip.open('/scratch3/armstrong/LST/d2020-02-12/Data/temp_%d.templates.gz' % n)
    input_dict = pickle.load(file_list)
    out_dict.update(input_dict)
    count+=1
    if count > 3:
        break

file_handler = gzip.open('/scratch3/armstrong/LST/d2020-02-12/Data/test2.templates.gz', "wb")
pickle.dump(out_dict, file_handler)
file_handler.close()