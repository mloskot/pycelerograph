"""
pycelerograph

Creates pretty reports with Bokeh graphs from Celero benchmark
results generated in CSV files.

Source: https://github.com/mloskot/pycelerograph
Author: Mateusz Loskot <mateusz@loskot.net>
License: http://unlicense.org
"""
import csv
import os
import sys
from enum import Enum
from bokeh.charts import Bar, output_file, reset_output, show
from bokeh.layouts import gridplot

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
                data[group_name] = {'file': os.path.basename(
                    csv_file), 'experiments': {}}

            experiments = data[group_name]['experiments']
            experiment_name = row[1]
            if experiment_name not in experiments:
                experiments[experiment_name] = {}

            experiment = experiments[experiment_name]
            for j, measure_name in enumerate(header[2:], 2):
                measure = Column.from_name(measure_name)
                assert measure is not None
                if measure not in experiment:
                    experiment[measure] = []
                series = experiment[measure]
                series.append(read_number(row[j]))

            # validate size of data series
            series_sizes = []
            for measure_name in header[2:]:
                measure = Column.from_name(measure_name)
                assert measure is not None
                series_sizes.append(len(experiment[measure]))
            assert series_sizes[1:] == series_sizes[:-1]
        return data

def plot_measure(group_name, experiments, measure):
    """Plots graph for single benchmark measurement of an experiment."""
    exp_sizes = []
    exp_names = []
    exp_results = []
    for experiment_name, experiment in experiments.items():
        measures_count = len(experiment[Column.problem_space])
        assert measures_count == len(experiment[measure])
        exp_names.extend([experiment_name] * measures_count)
        exp_sizes.extend(experiment[Column.problem_space])
        exp_results.extend(experiment[measure])
    assert len(exp_sizes) == len(exp_names) == len(exp_results)
    data = {
        'size': exp_sizes,
        'experiment': exp_names,
        measure.value: exp_results
    }
    plot = Bar(data, label='size', group='experiment', values=measure.value,
               legend='top_left', bar_width=10,
               title='Benchmark group: {0} - {1}'.format(
                   group_name, measure.value),
               xlabel='Problem space (size of input)',
               ylabel=measure.value)
    return plot


def generate_html_report(data, filename_prefix='celero_benchmark'):
    """Plots graphs with benchmark results."""
    assert data

    for group_name, group in data.items():
        html_file = '{}_{}.html'.format(filename_prefix, group_name)
        output_file(
            html_file, title="Benchmark results for '{}'".format(group_name))
        experiments = group['experiments']
        plots = [
            plot_measure(group_name, experiments, Column.baseline),
            plot_measure(group_name, experiments, Column.mean_time),
            plot_measure(group_name, experiments, Column.min_time),
            plot_measure(group_name, experiments, Column.max_time),
            plot_measure(group_name, experiments, Column.iteration_time),
            plot_measure(group_name, experiments, Column.iteration_per_sec)
        ]
        show(gridplot(plots, ncols=2, plot_width=600, plot_height=300))
        reset_output()

def main(csv_dir=None, csv_file=None):
    """Process CSV files into slick'n'sweet report with graphs."""
    csv_files = []
    if csv_file:
        csv_files.append(csv_file)
    if csv_dir:
        csv_files.extend([os.path.join(csv_dir, f)
                          for f in os.listdir(csv_dir) if f.endswith('.csv')])

    for filename in csv_files:
        data = read_results(filename)
        generate_html_report(data)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(
            'Usage: {0} <directory with benchmark .csv files>'.format(__file__))
    if os.path.isdir(sys.argv[1]):
        main(csv_dir=sys.argv[1])
    elif sys.argv[1].endswith('.csv') and os.path.isfile(sys.argv[1]):
        main(csv_file=sys.argv[1])
    else:
        sys.exit('\'{0}\' does not exist'.format(sys.argv[1]))
