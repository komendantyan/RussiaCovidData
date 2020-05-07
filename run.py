#!/usr/bin/env python3
# coding: utf-8

import pandas
import numpy

import matplotlib
from matplotlib import pyplot as plt
from datetime import timedelta


TITLE = 'Регионы с наибольшим числом заболевших'
YLABEL = 'Подтверждённые случаи'


def load_dataset():
    dataset = pandas.read_json('./corona.json')
    dataset.date = dataset.date.apply(pandas.to_datetime)
    dataset['index'] = dataset.date
    dataset = dataset.set_index('index')

    return dataset


def export_to_tables(dataset):
    dataset.to_csv('corona.csv')
    dataset.to_excel('corona.xls')


def top_regions(dataset, count=10):
    return list(dataset
                .sum()
                .drop(['total', 'total_healthy', 'total_reg', 'new_reg', 'new'])
                .sort_values(ascending=False)
                .head(count)
                .index)


def regression(series, slice_fit, slice_predict, name=None):
    from sklearn.linear_model import LinearRegression
    x = series.index.to_numpy().reshape(-1, 1).astype(int)
    y = numpy.log2(series.fillna(method='ffill').to_numpy())
    reg = LinearRegression()
    reg.fit(x[slice_fit], y[slice_fit])
    y_pred = 2**reg.predict(x[slice_predict])
    return pandas.Series(data=y_pred,
                         index=series.index[slice_predict],
                         name=(name or '??') + ' (тренд 4 дня назад)')


def get_series_to_plot(dataset):
    def cumsum(*columns):
        return sum(dataset[c].fillna(0.0) for c in columns)[::-1].cumsum()[::-1]

    regions = [reg
               for reg in top_regions(dataset)
               if reg not in {'Москва', 'Московская область', 'Санкт-Петербург', 'Ленинградская область'}]

    all_series = {}

    all_series['total'] = {'data': dataset.total,
                           'matplotlib': {'color': 'blue'}}

    all_series['Москва и МО'] = {'data': cumsum('Москва', 'Московская область'),
                                 'matplotlib': {'color': 'orange'}}

    all_series['Санкт-Петербург и ЛО'] = {'data': cumsum('Санкт-Петербург', 'Ленинградская область'),
                                                           'matplotlib': {'color': 'green'}}

    all_series.update(**{reg: cumsum(reg) for reg in regions})

    all_series['Россия без МО и ЛО'] = {
        'data': (
            all_series['total']['data'] -
            all_series['Москва и МО']['data'] -
            all_series['Санкт-Петербург и ЛО']['data']
        ),
        'matplotlib': {'color': 'magenta'}
    }

    all_series['total_healthy'] = {'data': dataset.total_healthy,
                                   'matplotlib': {'linestyle': '', 'marker': '+', 'color': 'red'}}

    for name in ['total', 'Москва и МО', 'Санкт-Петербург и ЛО', 'Россия без МО и ЛО']:
        all_series[name + ' linear'] = {'data': regression(all_series[name]['data'], slice(4, 11), slice(0, 11), name=name),
                                        'matplotlib': {'linestyle': '--', 'color': all_series[name]['matplotlib']['color']},
                                        'annotate': False}

    return all_series


def get_matplotlib_figure(all_series):
    fig, ax = plt.subplots(figsize=(20, 15), dpi=320)

    for name, series in all_series.items():
        if isinstance(series, dict):
            plot_params = series.get('matplotlib', {})
            params = series
            series = series['data']
        else:
            plot_params = {}
            params = {}

        series.plot(ax=ax, label=series.name or name, **plot_params)
        if params.get('annotate', True):
            ax.annotate(f'{series[0]} - {name}', (series.index[0], series[0]))

    ax.set_yscale('log', basey=2)
    ax.set_xticks(matplotlib.dates.drange(
        all_series['total']['data'].index.min(),
        all_series['total']['data'].index.max() + timedelta(2),
        timedelta(1)
    ))
    ax.xaxis.set_tick_params(rotation=70)
    ax.set_yticks(2**numpy.arange(numpy.ceil((numpy.log2(all_series['total']['data'].max()))) + 1))

    ax.grid(which='both')
    ax.legend(prop={'size': 16})
    ax.set_title(TITLE, size=32)
    ax.set_ylabel(YLABEL, size=16)
    ax.set_xlabel('')

    return fig


def main():
    dataset = load_dataset()
    export_to_tables(dataset)

    series = get_series_to_plot(dataset)

    fig = get_matplotlib_figure(series)
    fig.savefig('./plot.png')


if __name__ == "__main__":
    main()
