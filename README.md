# pycelerograph

Python utility to convert [Celero](https://github.com/DigitalInBlue/Celero) benchmark
results to pretty [Bokeh](http://bokeh.pydata.org/) graphs.

## Quickstart

Once you have built Celero runner for your benchmark, generate CSV report:

```
benchmark_cpp_sort -t benchmark_cpp_sort.csv
```

Then, generate HTML file with graphs:

```
python celerograph.py benchmark_cpp_sort.csv
```

See the [example](https://mloskot.github.io/pycelerograph/example/) for sample HTML output.

## Features

* Reads [Celero report in CSV](https://github.com/DigitalInBlue/Celero/blob/master/README.md) format into dictionary in memory.
* Generates single HTML report per benchmark group.
* Processes single CSV file or all CSV files in directory.
* Can also process single concatenated CSV file with multiple benchmark groups.
* Plots six graphs for the Celero measurements: *Baseline*, *us/Iteration*, *Iterations/sec*, *Min (us)*, *Max (us)*, *Mean (us)*.
* Plots the graphs in 2x3 grid layout.
* Plots bar charts only.
* Adds single [Bokeh toolbar](http://bokeh.pydata.org/en/latest/docs/user_guide/tools.html) at the top of HTML page.
* Is dead simple to modify, customise and extend.

### Features Plan

* Add tests. It is Python. It is shame to not to have any!
* Optimise format of the in-memory dictionary  to avoid re-aggregating of the measurements.
* Output the dictionary to JSON - currently, `class Column(Enum)` is not serializable with JSON encoder.

## License

This is free and unencumbered software released into the public domain.

http://unlicense.org

## Credits

* [John Farrier](https://github.com/DigitalInBlue/) for the Celero benchmarking library.
* [Bryan Van de Ven](https://github.com/bryevdv) for Bokeh discovery.
* [lexicalunit](https://github.com/lexicalunit) for [linking](https://github.com/lexicalunit/nanodbc/pull/258) me with Bryan.
