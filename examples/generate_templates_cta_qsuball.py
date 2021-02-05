"""
This file is a simple example of how to generate templates through all sets of simulation.
This should really only be taken as and example of how to use the classes provided,
although should probably work without too much hassle on most systems
"""
from argparse import ArgumentParser
import yaml
from template_builder.corsika_input import CORSIKAInput
from template_builder.simtelarray_config import SimTelArrayConfig, get_run_script
from template_builder.fit_templates import TemplateFitter
import os
from os import listdir
import multiprocessing
import gzip
import pickle


def get_file_list(directories):
    """
    Get the absolute locations of all files in a list of directories

    :param directories: list
        list of directories to check
    :return: list
        List of absolute file names
    """
    files_before_simulation = []

    for path in directories:
        for file in listdir(path):
            files_before_simulation.append(path + file)

    return files_before_simulation


def parse_config(file_list):
    """
    Parse required options from a list of configuration files

    :param file_list: list
        list of config files to parse
    :return: tuple
        Dictionaries of the required simulation inputs
    """

    corsika_dict = dict()
    simulation_input = dict()
    fit_input = dict()
    telescope_input = dict()

    # Loop over input config files
    for f in file_list:
        # Open YAML file
        with open(f[0], "r") as yaml_file:
            yaml_file = yaml.safe_load(yaml_file)

        # Get the config options if they exist
        if "CORSIKA" in yaml_file:
            corsika_dict.update(yaml_file["CORSIKA"])
        if "ShowerSimulation" in yaml_file:
            simulation_input.update(yaml_file["ShowerSimulation"])
        if "TelescopeSimulation" in yaml_file:
            telescope_input.update(yaml_file["TelescopeSimulation"])
        if "Fit" in yaml_file:
            fit_input.update(yaml_file["Fit"])

    return corsika_dict, simulation_input, telescope_input, fit_input


def write_corsika_input_cards(sim_telarray_directory, input_cards):
    """
    Save CORSIKA input cards from a dictionary in the directory provided

    :param sim_telarray_directory: str
        Base directory of sim_telarray package
    :param input_cards:  dict

    :return:
    """
    input_file_names = list()
    for card in input_cards:
        input_name = "input_altitude%.1f_azimuth%.1f_energy%.3f.input" % card
        file_name = sim_telarray_directory + "/corsika-run/" + input_name
        with open(file_name, "w") as input_file:
            input_file.write(input_cards[card])
            input_file.close()

        input_file_names.append(file_name)

    return input_file_names


def generate_templates():
    """
    main() function to call all steps of template production in series

    :return: None
    """

    # First Lets parse the command line
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', action='append', nargs=1,
                        metavar="config file",
                        help='Configuration YAML file locations')
    parser.add_argument('-o', '--output', default="test.templates.gz",
                        metavar="output file",
                        help='Name of output file')
    parser.add_argument('-m', '--cores', default=1, help='Number of cores to use for multiprocessing', type=int)
    parser.add_argument('--simulate-only', dest='simulate_only', action='store_true')
    parser.add_argument('--SGE', dest='SGE', action='store_true')

    args = parser.parse_args()

    # Followed by any config files
    corsika_input, simulation_input, telescope_input, fit_input = \
        parse_config(args.config)
    output_file = args.output

    print(corsika_input, simulation_input, telescope_input, fit_input)

    # Generate our range of CORSIKA input cards
    corsika = CORSIKAInput(input_parameters=corsika_input,
                           min_events=simulation_input["min_events"])

    cards = corsika.get_input_cards(simulation_input["event_number"],
                                    simulation_input["altitude"],
                                    simulation_input["azimuth"],
                                    simulation_input["energy_bins"],
                                    simulation_input["core_bins"],
                                    simulation_input["rotation_angle"],
                                    simulation_input["diameter"],
                                    get_run_script(telescope_input["config_name"])
                                    )
    # And write them in the sim_telarray directory
    corsika_input_file_names = \
        write_corsika_input_cards(telescope_input["sim_telarray_directory"], cards)

    # Then create the required sim_telearray telescope config files
    sim_telarray_config = SimTelArrayConfig(telescope_input["config_name"],
                                            telescope_input["config_file"],
                                            float(corsika_input["OBSLEV"]) / 100,
                                            telescope_input["atmosphere"],
                                            telescope_input["optical_efficiency"],
                                            telescope_input["extra_options"]
                                            )

    run_commands, output_paths = \
        sim_telarray_config.run_setup(telescope_input["sim_telarray_directory"],
                                      corsika_input_file_names)

    # Annoyingly sim_telarray doesn't let us choose our output file name (at least in
    # this script setup). So we instead look in output directory now and after our
    # simulations are complete and take the new files
    files_before = get_file_list(output_paths)

    # Submit to SGE cluster if we can
    if args.SGE:
        try:
            from submit_SGE import SubmitSGE
        except ImportError:
            print("submit_SGE package required for cluster submission")
        submit = SubmitSGE()
        submit.submit_job_list(run_commands,
                               telescope_input["config_name"] + "_temp")
    # Otherwise run on the command line
    else:
        tasks = []
        print('using %s out of %s cores' % (int(args.cores), multiprocessing.cpu_count()))
        pool = multiprocessing.Pool(int(args.cores))
        for command in run_commands:
            print("Running", command)
            # exit()
            tasks.append(command)
            # os.system(command)

        print(pool.map(os.system, tasks))
    print("Simulations complete")

    files_after = get_file_list(output_paths)
    # Create a list of newly created files
    files_after = list(set(files_after) - set(files_before))

    if len(files_after) == 0:
        print("No new simulation files created! Quitting before fit")
        return

    # tasks = []
    # fitter = TemplateFitter(min_fit_pixels=2000)
    #
    # templates = dict()
    # variance_templates = dict()
    #
    # for i in files_after:
    #     tasks.append([templates,variance_templates, i])
    # # Then generate our templates from these
    # pool.starmap(fitter.pool_generate_templates, tasks)
    #
    # fitter.pool_generate_templates(templates, variance_templates, files_after, output_file, max_events=50000)
    #
    # file_handler = gzip.open(output_file, "wb")
    # pickle.dump(templates, file_handler)
    # file_handler.close()

    fitter = TemplateFitter(min_fit_pixels=2000, verbose=True)
    pool = multiprocessing.Pool(int(args.cores))

    templates = dict()
    variance_templates = dict()

    tasks = []
    count = 0
    for n, i in enumerate(files_after):
        tasks.append([i, '/scratch3/armstrong/LST/d2020-02-12/Data/temp_%s.templates.gz' % n])
        count += 1
        # if count > 3:
        #     break
    pool.starmap(fitter.pool_generate_templates, tasks)

    out_dict = {}
    for n, i in enumerate(files_after):
        file_list = gzip.open('/scratch3/armstrong/LST/d2020-02-12/Data/temp_%d.templates.gz' % n)
        input_dict = pickle.load(file_list)
        out_dict.update(input_dict)

    file_handler = gzip.open('/scratch3/armstrong/LST/d2020-02-12/Data/LST-LaPalma-Prod5.templates.gz', "wb")
    pickle.dump(out_dict, file_handler)
    file_handler.close()

    return


if __name__ == "__main__":
    generate_templates()
