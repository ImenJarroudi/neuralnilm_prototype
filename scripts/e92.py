from __future__ import print_function, division
import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
from neuralnilm import Net, RealApplianceSource, BLSTMLayer, SubsampleLayer, DimshuffleLayer
from lasagne.nonlinearities import sigmoid, rectify
from lasagne.objectives import crossentropy, mse
from lasagne.init import Uniform, Normal
from lasagne.layers import LSTMLayer, DenseLayer, Conv1DLayer, ReshapeLayer
from lasagne.updates import adagrad, nesterov_momentum
from functools import partial
import os

NAME = "e92"
PATH = "/homes/dk3810/workspace/python/neuralnilm/figures"
SAVE_PLOT_INTERVAL=250

"""
Changes common to all these (compared to e91)
* on_power_thresh is now 20 watts for everything
* fixed max_appliance_powers and min_on_durations
* seq_length = 1500 (to fit in washer)
* min_on_durations increased for washer and dish washer
* skip_probability = 0.7
"""


def exp_a(name):
    """NaN after 31 epochs :("""
    print("e91d but with bigger net")
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=[300, 500, 200, 2500, 2400],
        on_power_thresholds=[20, 20, 20, 20, 20],
        min_on_durations=[60, 60, 60, 1800, 1800],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        min_off_duration=60,
        subsample_target=5,
        train_buildings=[1],
        validation_buildings=[1], skip_probability=0.7
    )

    net = Net(
        experiment_name=name + 'a',
        source=source,
        save_plot_interval=SAVE_PLOT_INTERVAL,
        loss_function=crossentropy,
        updates=partial(nesterov_momentum, learning_rate=0.01),
        layers_config=[
            {
                'type': DenseLayer,
                'num_units': 100,
                'nonlinearity': sigmoid,
                'W': Uniform(25),
                'b': Uniform(25)
            },
            {
                'type': DenseLayer,
                'num_units': 100,
                'nonlinearity': sigmoid,
                'W': Uniform(10),
                'b': Uniform(10)
            },
            {
                'type': BLSTMLayer,
                'num_units': 100,
                'W_in_to_cell': Uniform(5)
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)
            },
            {
                'type': Conv1DLayer,
                'num_filters': 150,
                'filter_length': 5,
                'stride': 5,
                'nonlinearity': sigmoid
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)
            },
            {
                'type': BLSTMLayer,
                'num_units': 200,
                'W_in_to_cell': Uniform(5)
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': sigmoid
            }
        ]
    )
    return net



def exp_b(name):
    """Results isn't learning anything very sensible.  I stopped it after 500 epochs."""
    print("e91d but with MSE cost (with sigmoid outputs)")
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=[300, 500, 200, 2500, 2400],
        on_power_thresholds=[20, 20, 20, 20, 20],
        min_on_durations=[60, 60, 60, 1800, 1800],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        min_off_duration=60,
        subsample_target=5,
        train_buildings=[1],
        validation_buildings=[1], skip_probability=0.7
    )

    net = Net(
        experiment_name=name + 'b',
        source=source,
        save_plot_interval=SAVE_PLOT_INTERVAL,
        loss_function=mse,
        updates=partial(nesterov_momentum, learning_rate=0.01),
        layers_config=[
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': sigmoid,
                'W': Uniform(25),
                'b': Uniform(25)
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': sigmoid,
                'W': Uniform(10),
                'b': Uniform(10)
            },
            {
                'type': BLSTMLayer,
                'num_units': 40,
                'W_in_to_cell': Uniform(5)
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)
            },
            {
                'type': Conv1DLayer,
                'num_filters': 60,
                'filter_length': 5,
                'stride': 5,
                'nonlinearity': sigmoid
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)
            },
            {
                'type': BLSTMLayer,
                'num_units': 80,
                'W_in_to_cell': Uniform(5)
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': sigmoid
            }
        ]
    )
    return net


def run_experiment(experiment):
    exp_name = 'exp_{:s}(NAME)'.format(experiment)
    print("***********************************")
    print("Running", exp_name, "...")
    net = eval(exp_name)
    net.print_net()
    net.compile()
    path = os.path.join(PATH, NAME+experiment)
    os.mkdir(path)
    os.chdir(path)
    try:
        net.fit(1501)
    except KeyboardInterrupt:
        print("Keyboard interrupt received.")
        response = raw_input("Save latest data [Y/n]? ")
        if not response or response.lower() == "y":
            print("Saving plots...")
            net.plot_estimates(save=True)
            net.plot_costs(save=True)
            print("Done saving plots")


def main():
    for experiment in list('ab'):
        try:
            run_experiment(experiment)
        except Exception as e:
            print("EXCEPTION:", e)


if __name__ == "__main__":
    main()
