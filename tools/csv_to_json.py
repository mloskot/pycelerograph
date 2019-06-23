"""
csv_to_json.py converts Celero CSV output to custom JSON.

Source: https://github.com/mloskot/pycelerograph
Author: Mateusz Loskot <mateusz@loskot.net>
License: http://unlicense.org
"""
import csv
import json
import os
import os.path
import sys
from enum import Enum

class Column(Enum):
    """Columns in Celero benchmark results report.
    """
    group = 'Group'
    experiment = 'Experiment'
    problem_space = 'Problem space'
    samples = 'Samples'
    iterations = 'Iterations'
    failure = 'Failure'
    baseline = 'Baseline'
    iteration_time = 'us/Iteration'
    iteration_per_sec = 'Iterations/sec'
    min_time = 'Min (us)'
    max_time = 'Max (us)'
    mean_time = 'Mean (us)'
    variance = 'Variance'
    stddev = 'Standard Deviation'
    skweness = 'Skewness'
    kurtosis = 'Kurtosis'
    zscore = 'Z Score'

    @classmethod
    def from_name(cls, column_name):
        """Gets column enumerator instance for given name."""
        for member in cls.__members__.values():
            if member.value.lower() == column_name.lower():
                return member

    @classmethod
    def is_name(cls, column_name):
        """Checks if column with given name exists."""
        for member in cls.__members__.values():
            if member.value.lower() == column_name.lower():
                return True
        return False

    def describe(self):
        # self is the member here
        return self.name, self.value

    def __str__(self):
        return '{0}'.format(self.value)

def read_results(csv_file):
    """Reads Celero benchmark measurements into dictionary."""
    assert os.path.isfile(csv_file), csv_file

    def read_number(string_value):
        """Reads string as float or int"""
        try:
            return int(string_value)
        except ValueError:
            return float(string_value)

    with open(csv_file) as file:
        print('Reading CSV:', csv_file)
        data = {}
        reader = csv.reader(file, skipinitialspace=True, quotechar="'")
        header = None
        for i, row in enumerate(reader):
            if i == 0:
                header = row
                continue
            # CSV report may contain header repeated between baseline groups
            # eg. if appended multiple CSV reports into one
            if Column.is_name(row[0]) and Column.is_name(row[1]):
                continue

            group_name = row[0]
            if group_name not in data:
                data[group_name] = {
                    'file': os.path.basename(csv_file),
                    'experiments': {}
                }

            experiments = data[group_name]['experiments']
            experiment_name = row[1]
            if experiment_name not in experiments:
                experiments[experiment_name] = {}

            experiment = experiments[experiment_name]
            for j, measure_name in enumerate(header[2:], 2):
                measure = Column.from_name(measure_name)
                assert measure is not None
                measure_str = str(measure)
                if measure_str not in experiment:
                    experiment[measure_str] = []
                series = experiment[measure_str]
                series.append(read_number(row[j]))

            # validate size of data series
            series_sizes = []
            for measure_name in header[2:]:
                measure = Column.from_name(measure_name)
                assert measure is not None
                measure_str = str(measure)
                series_sizes.append(len(experiment[measure_str]))
            assert series_sizes[1:] == series_sizes[:-1]
        return data

def main(csv_path):
    if not sys.argv[1].endswith('.csv') or not os.path.isfile(sys.argv[1]):
        sys.exit("'{0}' does not exist".format(sys.argv[1]))
    data = read_results(csv_path)

    json_path, ext = os.path.splitext(csv_path)
    json_path += '.json'
    print('Writing JSON:', json_path)
    with open(json_path, 'w') as outfile:
        json.dump(data, outfile)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: '{0}' <.csv file>".format(__file__))
    else:
        main(sys.argv[1])
