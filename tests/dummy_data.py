from dn3.data.dataset import *
from dn3.data.utils import min_max_normalize


START_POINT = 0
END_POINT = 10
SFREQ = 256
EVENTS = ((2, 3), (60, 2), (500, 1), (700, 3), (1200, 2), (2000, 1))

TMIN = 0
TLEN = 1.0

NUM_SESSIONS_PER_THINKER = 2
THINKERS_IN_DATASETS = 20
NUM_FOLDS = 5

# Creation Functions
# ------------------


def create_basic_data():
    sinx = np.sin(np.arange(START_POINT, END_POINT, 1 / SFREQ) * 10).astype('float')
    cosx = np.cos(np.arange(START_POINT, END_POINT, 1 / SFREQ) * 10).astype('float')
    events = np.zeros_like(sinx)
    for ev_sample, label in EVENTS:
        events[ev_sample] = label
    return np.array([sinx, cosx, events])


def create_dummy_raw():
    """
    Creates a Raw instance from `create_basic_data`
    Returns:
    -------
    raw : mne.io.Raw
    """
    data = create_basic_data()
    ch_names = [str(s) for s in range(2)] + ['STI 014']
    ch_types = ['eeg', 'eeg', 'stim']

    info = mne.create_info(ch_names=ch_names, sfreq=SFREQ, ch_types=ch_types)
    raw = mne.io.RawArray(data, info)

    return raw


def create_dummy_session(epoched=True, **kwargs):
    raw = create_dummy_raw()
    if epoched:
        events = mne.find_events(raw)
        epochs = mne.Epochs(raw, events, tmin=TMIN, tmax=TLEN + TMIN - 1 / SFREQ, baseline=None)
        return EpochTorchRecording(epochs, **kwargs)
    return RawTorchRecording(raw, TLEN, **kwargs)


def create_dummy_thinker(epoched=True, sessions_per_thinker=2, sess_args=dict(), **kwargs):
    session = create_dummy_session(epoched=epoched, **sess_args)
    return Thinker({'sess{}'.format(i): session.clone() for i in range(1, sessions_per_thinker + 1)},
                   return_session_id=True, **kwargs)


def create_dummy_dataset(epoched=True, sessions_per_thinker=2, num_thinkers=THINKERS_IN_DATASETS,
                         sess_args=dict(), thinker_args=dict(), **dataset_args):
    thinker = create_dummy_thinker(epoched=epoched, sessions_per_thinker=sessions_per_thinker, sess_args=sess_args,
                                   **thinker_args)
    return Dataset({"p{}".format(i): thinker.clone() for i in range(num_thinkers)}, **dataset_args)


# Check functions
# ---------------

def check_raw_against_data(retrieved, index):
    data = torch.from_numpy(create_basic_data())
    sample_len = int(TLEN * SFREQ)
    return torch.allclose(retrieved, min_max_normalize(data[:2, index:index+sample_len]).float())


def retrieve_underlying_dummy_data(event_index):
    data = torch.from_numpy(create_basic_data())
    sample = EVENTS[event_index][0]
    window = slice(int(sample - TMIN * SFREQ), int(sample + (TLEN + TMIN) * SFREQ))
    return min_max_normalize(data[:, window]).float()


def check_epoch_against_data(retrieved, event_index):
    return torch.allclose(retrieved, retrieve_underlying_dummy_data(event_index))
