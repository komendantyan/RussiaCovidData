#!/usr/bin/env python3
# coding: utf-8

import pandas
import numpy
from plotly import graph_objs as go

import matplotlib
from matplotlib import pyplot as plt
from datetime import datetime, timedelta


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


def get_series_to_plot(dataset):
    def cumsum(*columns):
        return sum(dataset[c].fillna(0.0) for c in columns)[::-1].cumsum()[::-1]

    regions = [reg
               for reg in top_regions(dataset)
               if reg not in {'Москва', 'Московская область', 'Санкт-Петербург', 'Ленинградская область'}]

    all_series = {
        'total': dataset.total,
        'Москва и МО': cumsum('Москва', 'Московская область'),
        'Санкт-Петербург и ЛО': cumsum('Санкт-Петербург', 'Ленинградская область'),

        **{reg: cumsum(reg) for reg in regions}
    }

    all_series['Россия без МО и ЛО'] = (
        all_series['total'] -
        all_series['Москва и МО'] -
        all_series['Санкт-Петербург и ЛО']
    )

    return all_series


def get_plotly_figure(all_series):
    fig = go.Figure(
        layout=go.Layout(
            yaxis=go.layout.YAxis(type='log', dtick=numpy.log10(2)),
            xaxis=go.layout.XAxis(dtick=24*3600*1000),
            title=TITLE,
            yaxis_title=YLABEL,
        )
    )

    for name, series in all_series.items():
        fig.add_trace(go.Scatter(
            x=all_series['total'].index,
            y=series,
            mode='lines+markers',
            name=name)
        )

    return fig


def get_matplotlib_figure(all_series):
    fig, ax = plt.subplots()

    for name, series in all_series.items():
        series.plot(ax=ax, label=name)
        ax.annotate(f'{series[0]} - {name}', (series.index[0], series[0]))

    ax.set_yscale('log', basey=2)
    ax.set_xticks(matplotlib.dates.drange(
        all_series['total'].index.min(),
        all_series['total'].index.max() + timedelta(2),
        timedelta(1)
    ))
    ax.set_yticks(2**numpy.arange((numpy.log2(all_series['total'].max()))))

    ax.grid(which='both')
    ax.legend(prop={'size': 16})
    ax.set_title(TITLE, size=32)
    ax.set_ylabel(YLABEL, size=16)

    return fig


def main():
    dataset = load_dataset()
    export_to_tables(dataset)

    series = get_series_to_plot(dataset)
    fig = get_plotly_figure(series)
    fig.write_html('./plot.html')

    fig = get_matplotlib_figure(series)
    fig.savefig('./plot.png')


if __name__ == "__main__":
    main()
