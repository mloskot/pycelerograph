"""
pycelerograph - generates pretty Bokeh graphs from Celero benchmark results.

Source: https://github.com/mloskot/pycelerograph
Author: Mateusz Loskot <mateusz@loskot.net>
License: http://unlicense.org

Creates pretty reports with Bokeh graphs from Celero benchmark
results generated in CSV files.

The script reads all CSV files in given directory or given single file
and converts to HTML with slick'n'sweet graphs using Bokeh.

Typically, each CSV file contains single benchmark group of data.
If a file is merges multiple groups, then multiple HTML reports
are generted, one for each group.

The script does not merge any reports.
"""
import csv
import os
import sys
from enum import Enum
from bokeh.io import output_file, reset_output, save, show
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.layouts import gridplot
from bokeh.palettes import Spectral10
from bokeh.plotting import figure
from bokeh.transform import factor_cmap

CELERO_PLOT_HEIGHT=400

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

def collect_experiments(group_name, experiments, measure):
    """Aggregates results of experiments for given measure (e.g. Baseline, Mean, etc.)."""
    data = {}
    for experiment_name, experiment in experiments.items():
        problem_space = experiment[Column.problem_space]
        assert len(problem_space) == len(experiment[measure])
        if 'sizes' not in data:
            data['sizes'] = experiment[Column.problem_space]
        if 'experiments' not in data:
            data['experiments'] = []
        data['experiments'].append(experiment_name)
        if 'results' not in data:
            data['results'] = []
        data['results'].append(experiment[measure])
    assert len(data['sizes']) == len(data['results'][0])
    assert len(data['experiments']) == len(data['results'])
    return data

def plot_measure(group_name, experiments, measure):
    """Plots graph for single benchmark measurement of an experiment."""
    d = collect_experiments(group_name, experiments, measure)
    assert len(d['sizes']) == len([r for r in zip(*d['results'])])
    x = [ (str(s), e) for s in d['sizes'] for e in d['experiments'] ]
    y = sum(zip(*d['results']), ()) # like an hstack
    source = ColumnDataSource(data=dict(x=x, y=y))
    title = 'Benchmark group: {0} - {1}'.format(group_name, measure.value)
    p = figure(x_range=FactorRange(*x), plot_height=CELERO_PLOT_HEIGHT, title=title)
    p.vbar(x='x', top='y', width=1, source=source,
           fill_color=factor_cmap('x', palette=Spectral10, factors=d['experiments'], start=1))
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    p.x_range.range_padding = 0.1
    p.xaxis.axis_label = 'Problem space (size of input)'
    p.xaxis.major_label_orientation = 'vertical'
    #p.xaxis.major_label_text_font_size = '0pt' # turn off x-axis tick labels
    p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
    p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.yaxis.axis_label = measure.value
    return p

def generate_html_reports(data, show_html=False):
    """Plots graphs with benchmark results.
    Creates HTML file for each benchmark group."""
    assert data

    html_files = []
    for group_name, group in data.items():
        csv_file = group['file']
        html_file = os.path.splitext(csv_file)[0]
        if group_name not in html_file:  # poor man attempt to avoid group name dups
            html_file += '_' + group_name
        html_file += '.html'

        print('Generating HTML:', html_file)
        experiments = group['experiments']
        #output_file(html_file, title="Benchmark results for '{}'".format(group_name))
        plots = [
            plot_measure(group_name, experiments, Column.baseline),
            plot_measure(group_name, experiments, Column.mean_time),
            plot_measure(group_name, experiments, Column.min_time),
            plot_measure(group_name, experiments, Column.max_time),
            plot_measure(group_name, experiments, Column.iteration_time),
            plot_measure(group_name, experiments, Column.iteration_per_sec)
        ]
        html_files.append((os.path.basename(csv_file), group_name, html_file))

        bokeh_obj = gridplot(plots, ncols=2, plot_width=600, plot_height=CELERO_PLOT_HEIGHT)
        if show_html:
            show(bokeh_obj)
        else:
            save(bokeh_obj, html_file)
        reset_output()
    return html_files

def generate_reports(csv_files):
    """Converts CSV reports in the list to HTML reports."""
    html_files = []
    for filename in csv_files:
        data = read_results(filename)
        html_files += generate_html_reports(data)

    with open('index.html', 'w') as index_file:
        print('Generating HTML: index.html')
        index_file.write("""<!DOCTYPE html><html>
        <head><title>Celero Benchmarks</title></head>
        <body>
        <h1>Celero Benchmarks</h1>
        <p>List of benchmark groups:</p>
        <ul>""")
        def a_tag(href, name):
            return '<a href="{0}">{1}</a>'.format(href, name)
        for csv_file, group_name, file_name in html_files:
            index_file.write('<li>')
            index_file.write(a_tag(file_name, group_name))
            index_file.write(' (<code>' + csv_file + '</code>)')
            index_file.write('</li>')
        index_file.write('</ul>')
        index_file.write('<hr />')
        index_file.write('Generated by ' +
            a_tag('https://github.com/mloskot/pycelerograph', 'pycelerograph'))
        index_file.write(' | ')
        index_file.write('Benchmark by ' +
            a_tag('https://github.com/DigitalInBlue/Celero', 'Celero'))
        index_file.write('</body></html>')

def main(csv_path):
    """Processing entry point."""
    if os.path.isdir(csv_path):
        csv_dir = csv_path
        csv_files = [
            os.path.join(csv_dir, f)
            for f in os.listdir(csv_dir) if f.endswith('.csv')]
    elif sys.argv[1].endswith('.csv') and os.path.isfile(sys.argv[1]):
        csv_files = [csv_path]
    else:
        sys.exit("'{0}' does not exist".format(sys.argv[1]))
    generate_reports(csv_files)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: '{0}' <directory with benchmark .csv files>".format(__file__))
    else:
        main(sys.argv[1])
