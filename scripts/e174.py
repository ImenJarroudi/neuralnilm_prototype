from __future__ import print_function, division
import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
from neuralnilm import Net, RealApplianceSource, BLSTMLayer, DimshuffleLayer
from lasagne.nonlinearities import sigmoid, rectify
from lasagne.objectives import crossentropy, mse
from lasagne.init import Uniform, Normal
from lasagne.layers import LSTMLayer, DenseLayer, Conv1DLayer, ReshapeLayer, FeaturePoolLayer
from neuralnilm.updates import nesterov_momentum
from functools import partial
import os
from neuralnilm.source import standardise, discretize, fdiff, power_and_fdiff
from neuralnilm.experiment import run_experiment
from neuralnilm.net import TrainingError
import __main__

NAME = os.path.splitext(os.path.split(__main__.__file__)[1])[0]
PATH = "/homes/dk3810/workspace/python/neuralnilm/figures"
SAVE_PLOT_INTERVAL = 250
GRADIENT_STEPS = 100

"""
e103
Discovered that bottom layer is hardly changing.  So will try
just a single lstm layer

e104
standard init
lower learning rate

e106
lower learning rate to 0.001

e108
is e107 but with batch size of 5

e109
Normal(1) for BLSTM

e110
* Back to Uniform(5) for BLSTM
* Using nntools eb17bd923ef9ff2cacde2e92d7323b4e51bb5f1f
RESULTS: Seems to run fine again!

e111
* Try with nntools head
* peepholes=False
RESULTS: appears to be working well.  Haven't seen a NaN, 
even with training rate of 0.1

e112
* n_seq_per_batch = 50

e114
* Trying looking at layer by layer training again.
* Start with single BLSTM layer

e115
* Learning rate = 1

e116
* Standard inits

e117
* Uniform(1) init

e119
* Learning rate 10
# Result: didn't work well!

e120
* init: Normal(1)
* not as good as Uniform(5)

e121
* Uniform(25)

e122
* Just 10 cells
* Uniform(5)

e125
* Pre-train lower layers

e128
* Add back all 5 appliances
* Seq length 1500
* skip_prob = 0.7

e129
* max_input_power = None
* 2nd layer has Uniform(5)
* pre-train bottom layer for 2000 epochs
* add third layer at 4000 epochs

e131

e138
* Trying to replicate e82 and then break it ;)

e140
diff

e141
conv1D layer has Uniform(1), as does 2nd BLSTM layer

e142
diff AND power

e144
diff and power and max power is 5900

e145
Uniform(25) for first layer

e146
gradient clip and use peepholes

e147
* try again with new code

e148
* learning rate 0.1

e150
* Same as e149 but without peepholes and using BLSTM not BBLSTM

e151
* Max pooling

171
lower learning rate

172
even lower learning rate

173
slightly higher learning rate!
"""


def scaled_cost(x, t):
    raw_cost = (x - t) ** 2
    energy_per_seq = t.sum(axis=1)
    energy_per_batch = energy_per_seq.sum(axis=1)
    energy_per_batch = energy_per_batch.reshape((-1, 1))
    normaliser = energy_per_seq / energy_per_batch
    cost = raw_cost.mean(axis=1) * (1 - normaliser)
    return cost.mean()

def exp_a(name):
    # 151d but training for much longer and skip prob = 0.7
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=None,#[200, 100, 200, 2500, 2400],
        on_power_thresholds=[5, 5, 5, 5, 5],
        max_input_power=5900,
        min_on_durations=[60, 60, 60, 1800, 1800],
        min_off_durations=[12, 12, 12, 1800, 600],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        train_buildings=[1],
        validation_buildings=[1], 
        skip_probability=0.7,
        n_seq_per_batch=25,
        include_diff=True
    )

    net = Net(
        experiment_name=name,
        source=source,
        save_plot_interval=1000,
        loss_function=scaled_cost,
        updates=partial(nesterov_momentum, learning_rate=.0000001, clip_range=(-1, 1)),
        layers_config=[
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(25),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': rectify
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': None,
                'W': Uniform(25)
            }
        ]
    )
    return net



def exp_b(name):
    # A but with sigmoid penultimate layer
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=None,#[200, 100, 200, 2500, 2400],
        on_power_thresholds=[5, 5, 5, 5, 5],
        max_input_power=5900,
        min_on_durations=[60, 60, 60, 1800, 1800],
        min_off_durations=[12, 12, 12, 1800, 600],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        train_buildings=[1],
        validation_buildings=[1], 
        skip_probability=0.7,
        n_seq_per_batch=25,
        include_diff=True
    )

    net = Net(
        experiment_name=name,
        source=source,
        save_plot_interval=1000,
        loss_function=scaled_cost,
        updates=partial(nesterov_momentum, learning_rate=.0000001, clip_range=(-1, 1)),
        layers_config=[
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(25),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': sigmoid
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': None,
                'W': Uniform(25)
            }
        ]
    )
    return net



def exp_c(name):
    # A but with 3 BBLSTM layers
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=None,#[200, 100, 200, 2500, 2400],
        on_power_thresholds=[5, 5, 5, 5, 5],
        max_input_power=5900,
        min_on_durations=[60, 60, 60, 1800, 1800],
        min_off_durations=[12, 12, 12, 1800, 600],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        train_buildings=[1],
        validation_buildings=[1], 
        skip_probability=0.7,
        n_seq_per_batch=25,
        include_diff=True
    )

    net = Net(
        experiment_name=name,
        source=source,
        save_plot_interval=1000,
        loss_function=scaled_cost,
        updates=partial(nesterov_momentum, learning_rate=.0000001, clip_range=(-1, 1)),
        layers_config=[
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(25),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': rectify
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': None,
                'W': Uniform(25)
            }
        ]
    )
    return net




def exp_d(name):
    # A but with downsampling 3x
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=None,#[200, 100, 200, 2500, 2400],
        on_power_thresholds=[5, 5, 5, 5, 5],
        max_input_power=5900,
        min_on_durations=[60, 60, 60, 1800, 1800],
        min_off_durations=[12, 12, 12, 1800, 600],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        train_buildings=[1],
        validation_buildings=[1], 
        skip_probability=0.7,
        n_seq_per_batch=25,
        include_diff=True,
        subsample_target=3,
        input_padding=2
    )

    net = Net(
        experiment_name=name,
        source=source,
        save_plot_interval=1000,
        loss_function=scaled_cost,
        updates=partial(nesterov_momentum, learning_rate=.0000001, clip_range=(-1, 1)),
        layers_config=[
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(25),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)  # (batch, features, time)
            },
            {
                'type': Conv1DLayer, # convolve over the time axis
                'num_filters': 50,
                'filter_length': 3,
                'stride': 1,
                'nonlinearity': sigmoid,
                'W': Uniform(1)
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1) # back to (batch, time, features)
            },
            {
                'type': FeaturePoolLayer,
                'ds': 3, # number of feature maps to be pooled together
                'axis': 1 # pool over the time axis
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': rectify
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': None,
                'W': Uniform(25)
            }
        ]
    )
    return net



def exp_e(name):
    # D but with downsampling 5x
    source = RealApplianceSource(
        filename='/data/dk3810/ukdale.h5',
        appliances=[
            ['fridge freezer', 'fridge', 'freezer'], 
            'hair straighteners', 
            'television',
            'dish washer',
            ['washer dryer', 'washing machine']
        ],
        max_appliance_powers=None,#[200, 100, 200, 2500, 2400],
        on_power_thresholds=[5, 5, 5, 5, 5],
        max_input_power=5900,
        min_on_durations=[60, 60, 60, 1800, 1800],
        min_off_durations=[12, 12, 12, 1800, 600],
        window=("2013-06-01", "2014-07-01"),
        seq_length=1500,
        output_one_appliance=False,
        boolean_targets=False,
        train_buildings=[1],
        validation_buildings=[1], 
        skip_probability=0.7,
        n_seq_per_batch=25,
        include_diff=True,
        subsample_target=5,
        input_padding=4
    )

    net = Net(
        experiment_name=name,
        source=source,
        save_plot_interval=1000,
        loss_function=scaled_cost,
        updates=partial(nesterov_momentum, learning_rate=.0000001, clip_range=(-1, 1)),
        layers_config=[
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(25),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1)  # (batch, features, time)
            },
            {
                'type': Conv1DLayer, # convolve over the time axis
                'num_filters': 50,
                'filter_length': 5,
                'stride': 1,
                'nonlinearity': sigmoid,
                'W': Uniform(1)
            },
            {
                'type': DimshuffleLayer,
                'pattern': (0, 2, 1) # back to (batch, time, features)
            },
            {
                'type': FeaturePoolLayer,
                'ds': 5, # number of feature maps to be pooled together
                'axis': 1 # pool over the time axis
            },
            {
                'type': BLSTMLayer,
                'num_units': 50,
                'W_in_to_cell': Uniform(1),
                'gradient_steps': GRADIENT_STEPS,
                'peepholes': False
            },
            {
                'type': DenseLayer,
                'num_units': 50,
                'nonlinearity': rectify
            },
            {
                'type': DenseLayer,
                'num_units': source.n_outputs,
                'nonlinearity': None,
                'W': Uniform(25)
            }
        ]
    )
    return net




def init_experiment(experiment):
    full_exp_name = NAME + experiment
    func_call = 'exp_{:s}(full_exp_name)'.format(experiment)
    print("***********************************")
    print("Preparing", full_exp_name, "...")
    net = eval(func_call)
    return net


def main():
    for experiment in list('abcde'):
        full_exp_name = NAME + experiment
        path = os.path.join(PATH, full_exp_name)
        try:
            net = init_experiment(experiment)
            run_experiment(net, path, epochs=10000)
        except KeyboardInterrupt:
            break
        except TrainingError as exception:
            print("EXCEPTION:", exception)
        except Exception as exception:
            raise
            print("EXCEPTION:", exception)
            import ipdb; ipdb.set_trace()


if __name__ == "__main__":
    main()
