# needed
import os
import re
import soundfile as sf
from IPython.display import Audio
from IPython.display import display
import numpy as np
# recommended ...
from scipy import signal
from scipy.io import wavfile
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter
from collections import defaultdict
import pickle
from scipy.fft import fft, ifft, fftfreq
import scipy.io
import matplotlib.pyplot as plt
from matplotlib import cm
from typing import Optional
import time
from tqdm import tqdm

# SETTINGS
SAMPLE_RATE = 16000
NFFT = 2048
FRAME_DURATION = 0.1  # in seconds

NPERFRAME = int(SAMPLE_RATE * FRAME_DURATION)
NOVERLAP = NPERFRAME // 8

# parameters for peak extraction
NEIGHBORHOOD_SIZE = (25, 25)  # size of the neighborhood to consider for max filtering
PEAKS_TO_KEEP = 256  # maximum number of peaks to keep for each spectrogram

# fingerprinting parameters
TARGET_ZONE_OFFSET = 0.1  # seconds
TARGET_ZONE_DURATION = 1.8 # seconds
TARGET_ZONE_FREQUENCY_BAND = 4500  # Hz

# parameters for fingerprint storage
LOAD_FROM_FILE = False  # if True, load existing file-based storage of fingerprints, 
                        # else use in-memory dictionary that has to be rebuilt each time        
SAVE_TO_FILE = True  # if True, save fingerprint database to file after building

FILE_NAME = "fingerprint.pkl"


# print parameters
print("==============PARAMETERS============")
print(f"CWD = {os.getcwd()}" )
print(f"SAMPLE RATE = {SAMPLE_RATE}" )
print(f"NFFT = {NFFT}" )
print(f"FRAME DURATION (s) = {FRAME_DURATION}" )
print(f"SAMPLES PER FRAME = {NPERFRAME}" )
print(f"OVERLAP (SAMPLES) = {NOVERLAP}" )
print(f"NEIGHBORHOOD SIZE = {NEIGHBORHOOD_SIZE}" )
print(f"PEAKS TO KEEP = {PEAKS_TO_KEEP}" )
print("===============STORAGE=============")
print(f"LOAD FROM FILE = {LOAD_FROM_FILE}" )
print(f"SAVE TO FILE = {SAVE_TO_FILE}" )
print(f"FILE NAME = {FILE_NAME}" )



# load the known data - the function returns a big matrix with all the signals
def load_data (S, dirname, count, no_samples):
  ii = 0
  for one in np.arange(count):
    S[ii], Fs = sf.read(dirname + "/" + str(one) + ".wav")
    ii = ii+1

# HELPER FUNCTIONS
def my_spectrogram(signal):
    """
    Compute spectrogram of the given signal. Uses scipy.signal spectrogram function.
    """
    return spectrogram(signal, fs=SAMPLE_RATE, nperseg=NPERFRAME, noverlap=NOVERLAP, nfft=NFFT)

def plot_spectrogram(f, t, Sxx, peaks=None, ax=None, vmin=-160):
    """
    Plot spectrogram with optional peaks overlay.
    
    Parameters:
    - f: frequency array
    - t: time array
    - Sxx: spectrogram power array
    - peaks: optional list of peaks (freq_idx, time_idx, magnitude)
    - ax: optional matplotlib axis object. If None, creates new figure
    
    Returns:
    - mesh: the pcolormesh object (useful for adding colorbar)
    """
    Sxx_log = 10 * np.log10(Sxx + 1e-20)  # Convert to dB scale
    
    # Create new figure if ax not provided
    if ax is None:
        plt.figure(figsize=(10, 4))
        ax = plt.gca()
    
    # Plot spectrogram
    mesh = ax.pcolormesh(t, f, Sxx_log, shading='gouraud', cmap=cm.inferno, vmin=vmin)
    
    # Plot peaks AFTER the spectrogram so they appear on top
    if peaks is not None:
        peak_freqs = peaks[:, 0]
        peak_times = peaks[:, 1]
        ax.scatter(peak_times, peak_freqs, c='blue', s=10, marker='x', linewidths=1)
    
    ax.set_ylabel('Frequency [Hz]')
    ax.set_xlabel('Time [s]')
    ax.set_title('Spectrogram')
    ax.set_xlim(min(t), max(t))
    
    # Only show the plot if we created a new figure
    if ax is None:
        cbar = plt.colorbar(mesh)
        cbar.set_label('Power spectral density [dB]', rotation=270, labelpad=15)
        plt.show()
    
    return mesh

def extract_peaks(f, t,Sxx, filter_size= NEIGHBORHOOD_SIZE, peaks_to_keep=PEAKS_TO_KEEP):
    """Extracts peaks from a spectrogram using local maximum filtering."""
    # Apply local maximum filter
    local_max = maximum_filter(Sxx, size=filter_size)
    
    # Find where the spectrogram equals the local maximum (these are the real peaks)
    peak_mask = (Sxx == local_max)

    # get peak coordinates and magnitudes
    freq_idx, time_idx = np.where(peak_mask)
    magnitudes = Sxx[freq_idx, time_idx]

    # Sort peaks by magnitude in descending order
    sorted_mag_idx = np.flip(np.argsort(magnitudes))
    
    npeaks = len(sorted_mag_idx)
    # print(f"Found {npeaks} peaks in the spectrogram.")

    # Apply limit to number of peaks
    if npeaks > peaks_to_keep:
        # print(f"Using only {peaks_to_keep} peaks.")
        sorted_mag_idx = sorted_mag_idx[0:peaks_to_keep]


    freq_idx = freq_idx[sorted_mag_idx]
    time_idx = time_idx[sorted_mag_idx]
    # magnitudes = magnitudes[sorted_mag_idx]

    # Combine everything into list of tuples
    peaks_idx = np.zeros([len(sorted_mag_idx),2], dtype=int)
    peaks_idx[:,0] = freq_idx  
    peaks_idx[:,1] = time_idx
    
    peaks = np.zeros([len(sorted_mag_idx),2], dtype=float)
    peaks[:,0] = f[freq_idx]
    peaks[:,1] = t[time_idx]
    
    return peaks_idx, peaks

def target_zone_search(anchor: np.ndarray, peaks: np.ndarray):
    """Finds peaks within the target zone defined relative to the anchor peak."""
    target_zone_peaks = []
    anchor_freq, anchor_time = anchor
    
    # Define target zone boundaries
    time_start = anchor_time + TARGET_ZONE_OFFSET
    time_end = time_start + TARGET_ZONE_DURATION
    freq_limit_upper = anchor_freq + TARGET_ZONE_FREQUENCY_BAND/2
    freq_limit_lower = anchor_freq - TARGET_ZONE_FREQUENCY_BAND/2
    target_zone = np.array([time_start, time_end, freq_limit_lower, freq_limit_upper])

    # Search for peaks within the target zone
    for peak in peaks:
        peak_freq, peak_time = peak
        if (time_start <= peak_time <= time_end) and (freq_limit_lower <= peak_freq <= freq_limit_upper):
            target_zone_peaks.append(peak)

    # Convert list to numpy array for easier manipulation
    target_zone_peaks = np.array(target_zone_peaks)
    
    return target_zone_peaks, target_zone

def generate_hashes(peaks, song_index: Optional[int] = None):
    """Generates fingerprint hashes from the list of peaks (constellation map). 
    For registration song_index must be provided and for identification leave song_index as None."""

    num_peaks = peaks.shape[0]
    n = np.arange(0, num_peaks)
    hash_list = []

    # for each anchor peak find target zone peaks and generate hashes
    for anchor_idx in n:
        anchor = peaks[anchor_idx]
        target_zone_peaks, _ = target_zone_search(anchor, peaks)

        if target_zone_peaks.size == 0:  # no peaks in target zone
            continue
        
        for target_peak in target_zone_peaks:
            freq1 = int(anchor[0])
            freq2 = int(target_peak[0])
            t1 = int(anchor[1] * 100)             # convert to centiseconds 
            t2 = int(target_peak[1] * 100)        # convert to centiseconds
            delta_t = t2 - t1
            hash_value = hash((freq1, freq2, delta_t))

            if song_index is not None:
                hash_list.append((hash_value, t1, song_index))
            else:
                hash_list.append((hash_value, t1))

    return hash_list

def generate_fingerprint(signal, song_index: Optional[int] = None):
    """Generates fingerprint hashes for a single signal. 
    For registration song_index must be provided and for identification leave song_index as None."""
    f, t, Sxx = my_spectrogram(signal)
    _, peaks = extract_peaks(f, t, Sxx)
    return generate_hashes(peaks, song_index=song_index)

def build_fingerprint_database(known_signals, load_from_file: Optional[bool] = False, save_to_file: Optional[bool] = True, filename: Optional[str] ="fingerprint.pkl"):
    """Build hash database from all known songs."""
    
    fingerprint_db = defaultdict(list)  # {hash_value: [(time_offset, song_index)]}
    
    # if file-based storage is used, try to load existing database, else build new one
    if load_from_file:
        if os.path.exists(filename):
            print("Loading fingerprint database from file...")
            fingerprint_db = load_fingerprint_db_pickle(filename)
            print(f"Total unique hashes: {len(fingerprint_db)}")
            return fingerprint_db
        else:
            print("Fingerprint database file not found. Building new database...")

    start_time = time.time()
    
    # TQDM for progress bar :) 
    for idx in tqdm(range(len(known_signals)), desc="Building database", unit="song"):
        hashes = generate_fingerprint(known_signals[idx], song_index=idx)
        
        # add hashes to the database
        for hash_value, time_offset, song_index in hashes:
            fingerprint_db[hash_value].append((time_offset, song_index))
    
    end_time = time.time()
    print(f"\nDatabase built in {end_time - start_time:.2f} seconds")
    print(f"Total unique hashes: {len(fingerprint_db)}")
    
    # save database to file
    if save_to_file:
        save_fingerprint_db_pickle(fingerprint_db, filename=filename)

    return fingerprint_db

def save_fingerprint_db_pickle(fingerprint_db, filename: Optional[str] = "fingerprint.pkl"):
    """Save fingerprint database using pickle."""
    with open(filename, 'wb') as f:
        pickle.dump(fingerprint_db, f)
    print(f"Fingerprint database saved to {filename}")

def load_fingerprint_db_pickle(filename: str ="fingerprint.pkl"):
    """Load fingerprint database from pickle file."""
    with open(filename, 'rb') as f:
        fingerprint_db = pickle.load(f)
    print(f"Fingerprint database loaded from {filename}")
    print(f"Total unique hashes: {len(fingerprint_db)}")
    return fingerprint_db

def recognize_signal(input_signal, fingerprint_db):
    """Recognize the song from the given signal using the fingerprint database."""
    query_hashes = generate_fingerprint(input_signal)
    matches = defaultdict(int)  # {song_index: count_of_matching_hashes}

    # for each hash in the signal, check if it exists in the database
    for hash_value, _ in query_hashes:
        if hash_value in fingerprint_db:
            entries = fingerprint_db[hash_value]
            for _, song_index in entries:
                matches[song_index] += 1
    
    return matches

def recognize_signal_time_offset(input_signal, fingerprint_db):
    """Recognize the song from the given signal using the fingerprint database with time offset alignment."""
    query_hashes = generate_fingerprint(input_signal)
    
    # {song_id: {time_offset_diff: count}}
    offset_matches = defaultdict(lambda: defaultdict(int))
    
    for query_hash_value, query_time in query_hashes:
        if query_hash_value in fingerprint_db:
            for db_time, song_id in fingerprint_db[query_hash_value]:
                
                #calculate time diff between db hash and query hash
                time_diff = db_time - query_time
                
                # Round time difference to nearest decisecond for robustness
                time_diff_rounded = round(time_diff / 10) * 10

                #Count the occurrence of this time offset for particular song
                offset_matches[song_id][time_diff_rounded] += 1
    
    # For each song, find the most common time offset
    best_matches = {}
    for song_id, offsets in offset_matches.items():
        # Most common offset = likely position of query in the song
        best_offset = max(offsets, key=offsets.get)  #get offset with max count 
        match_count = offsets[best_offset]
        best_matches[song_id] = (match_count, best_offset)
    
    return best_matches

def compute_similarity_matrix(signals, fingerprint_db , N_signals: int, N_known: int):
    """Compute similarity matrix between valid and known signals."""
    similarities = np.zeros((N_signals, N_known), dtype=int)

    # for each validation/test signal, create scores and fill the similarity matrix
    for signal_id in tqdm(range(N_signals) , desc="Computing similarities", unit="validation signal"):
        recognized_song = recognize_signal(signals[signal_id], fingerprint_db)
        for song_index, match_count in recognized_song.items():
            similarities[signal_id, song_index] = match_count

    return similarities

def compute_similarity_matrix_time_offsets(signals, fingerprint_db , N_signals: int, N_known: int):
    """Compute similarity matrix between valid and known signals."""
    similarities = np.zeros((N_signals, N_known), dtype=int)
    time_offsets = np.zeros((N_signals, N_known), dtype=int)

    # for each validation/test signal, create scores and fill the similarity matrix
    for signal_id in tqdm(range(N_signals) , desc="Computing similarities", unit="validation signal"):
        recognized_songs = recognize_signal_time_offset(signals[signal_id], fingerprint_db)

        for song_id, (match_count, time_offset) in recognized_songs.items():
            similarities[signal_id, song_id] = match_count
            time_offsets[signal_id, song_id] = time_offset 
    return similarities, time_offsets




def eval(scores, key):
    indices = np.flip(np.argsort(scores), axis=-1) # we want highest to lowest ...
    #print(scores[0,key[0]], key[0], indices)
    top1acc = np.sum(key == indices[:,0]) / indices.shape[0]
    top5acc = 0
    for ii in range(5):
        top5acc += np.sum(key == indices[:,ii])
    top5acc /=  indices.shape[0]
    return top1acc, top5acc


if __name__ == "__main__":

    # load known data
    N_known = 706; duration_known = 10; 
    no_samples_known = SAMPLE_RATE * duration_known
    known_signals=np.zeros([N_known, no_samples_known]); 
    load_data(known_signals, "proj/known", N_known, no_samples_known) #remove proj/
    # display(Audio(known_signals[45], rate=SAMPLE_RATE))

    # load validation data
    N_valid = 50; duration_valid = 5; 
    no_samples_valid = SAMPLE_RATE * duration_valid
    valid_signals=np.zeros([N_valid, no_samples_valid]); 
    load_data(valid_signals, "proj/valid", N_valid, no_samples_valid)  #remove proj/
    # display(Audio(valid_signals[45], rate=SAMPLE_RATE))

    # load test data
    N_test = 50; duration_test = 5;
    no_samples_test = SAMPLE_RATE * duration_test
    test_signals=np.zeros([N_test, no_samples_test]); 
    load_data(test_signals, "proj/239026", N_test, no_samples_test)


    song_index = 18
    # load key
    key = np.loadtxt("proj/valid/key.txt", delimiter = ',', usecols=(1), dtype ='int')
  
    # PHASE1

    # fig, (ax1,ax2) = plt.subplots(2, 1, figsize=(12, 8))
    # First spectrogram
    # f1, t1, Sxx1 = my_spectrogram(known_signals[key[song_index]][0:SAMPLE_RATE*5])

    # f1, t1, Sxx1 = my_spectrogram(valid_signals[song_index])
    # peaks1_idx,  peaks1 = extract_peaks(f1, t1, Sxx1)
    # mesh1 = plot_spectrogram(f1, t1, Sxx1, peaks1, ax=ax1)
    # ax1.set_title(f'Valid signal #{song_index}')
    # ax1.set_aspect('auto') 
    # plt.colorbar(mesh1, ax=ax1, label='PSD [dB]')

    # # second spectrogram
    # f2, t2, Sxx2 = my_spectrogram(known_signals[key[song_index]])
    # peaks2_idx, peaks2 = extract_peaks(f2, t2, Sxx2)
    # mesh2 = plot_spectrogram(f2, t2, Sxx2, peaks2, ax=ax2)
    # ax2.set_title(f'Known signal #{key[song_index]}, matched to valid signal #{song_index}')
    # ax2.set_aspect('auto') 
    # plt.colorbar(mesh2, ax=ax2, label='PSD [dB]')
    # plt.tight_layout()


    # PHASE2

    # anchor_id  = 21

    # f1, t1, Sxx1 = my_spectrogram(valid_signals[song_index])
    # _,  peaks1 = extract_peaks(f1, t1, Sxx1)
    # plt.figure(figsize=(10, 4))
    # plt.scatter(peaks1[:,1], peaks1[:,0], c='blue', s=10, marker='x', linewidths=1)

    # target_zone_peaks, target_zone = target_zone_search(peaks1[anchor_id], peaks1)

    # plt.scatter(peaks1[anchor_id,1], peaks1[anchor_id,0], c='green', s=50, marker='*', linewidths=1)

    # if target_zone_peaks.size > 0:
    #     plt.scatter(target_zone_peaks[:,1], target_zone_peaks[:,0], c='red', s=20, marker='o', linewidths=1)
    # plt.plot([target_zone[0], target_zone[1], target_zone[1], target_zone[0], target_zone[0]],
    #          [target_zone[2], target_zone[2], target_zone[3], target_zone[3], target_zone[2]], 'g--', linewidth=1)
    # plt.xlabel('Time [s]')
    # plt.ylabel('Frequency [Hz]')
    # plt.title(f'Peaks from valid signal #{song_index}')
    # plt.show()

    # PHASE3 
    # known_id = 45
    # start_time = time.time()
    # hashes = generate_fingerprint(known_signals[known_id], song_index=known_id)
    # print(f"Generated {len(hashes)} hashes for known signal #{known_id}")

    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"Fingerprint generation took {elapsed_time:.4f} seconds")

    # PHASE4
    # fingerprint_db = build_fingerprint_database(known_signals, load_from_file=LOAD_FROM_FILE, save_to_file=SAVE_TO_FILE, filename=FILE_NAME)
    # for hash_value in list(fingerprint_db.keys())[:5]:
    #     print(f"Hash: {hash_value}, Entries: {fingerprint_db[hash_value]}")

    # PHASE 5
    # fingerprint_db = load_fingerprint_db_pickle("fingerprint.pkl")
    # print(f"Fingerprint database contains {len(fingerprint_db)} unique hashes.")
    # for hash_value in list(fingerprint_db.keys())[:5]:
    #     print(f"Hash: {hash_value}, Entries: {fingerprint_db[hash_value]}")

    # valid_id = 18
    # recognized_song = recognize_signal(valid_signals[valid_id], fingerprint_db)

    # PHASE 6
    fingerprint_db = build_fingerprint_database(known_signals, load_from_file=LOAD_FROM_FILE, save_to_file=SAVE_TO_FILE, filename=FILE_NAME)
    start_time = time.time()
    scores_matrix = compute_similarity_matrix(valid_signals, fingerprint_db , N_valid, N_known)
    end_time = time.time()
    print(f"Similarity matrix computed in {end_time - start_time:.2f} seconds")
    print("Similarity matrix shape:", scores_matrix.shape)
    #
    top1, top5 = eval(scores_matrix, key)
    print("Top 1 accuracy ", top1 * 100, "%, Top 5 accuracy ", top5 * 100, "%" )

    # Najdi predikce pro každou validační píseň
    predictions = np.argmax(scores_matrix, axis=1)  # Index nejvyšší hodnoty v každém řádku
    match_counts = np.max(scores_matrix, axis=1)    # Nejvyšší počet shod

    # Porovnej s klíčem
    correct_mask = (predictions == key)
    correct_predictions = predictions[correct_mask]

    print(f"Correct predictions: {len(correct_predictions)} out of {N_valid}")
    for i in range(N_valid):
        print(f"Validation song {i}: Predicted = {predictions[i]}, Actual = {key[i]}, Matches = {match_counts[i]}")
    incorrect_predictions = predictions[~correct_mask]
    print(f"Incorrect predictions: {len(incorrect_predictions)} out of {N_valid}")
    for i in range(N_valid):
        if predictions[i] != key[i]:
            print(f"Validation song {i}: Predicted = {predictions[i]}, Actual = {key[i]}, Matches = {match_counts[i]}")

        
    # PHASE 7 test data
    # fingerprint_db = build_fingerprint_database(known_signals, load_from_file=LOAD_FROM_FILE, save_to_file=SAVE_TO_FILE, filename=FILE_NAME)
    # pred_key = np.loadtxt("predictions_key.txt", delimiter = ',', usecols=(1), dtype ='int')
    # start_time = time.time()
    # scores_matrix = compute_similarity_matrix(test_signals, fingerprint_db , N_test, N_known)
    # end_time = time.time()
    # print(f"Similarity matrix computed in {end_time - start_time:.2f} seconds")
    # print("Similarity matrix shape:", scores_matrix.shape)

    # top1, top5 = eval(scores_matrix, pred_key)
    # print("Top 1 accuracy ", top1 * 100, "%, Top 5 accuracy ", top5 * 100, "%" )

    # # Najdi predikce pro každou validační píseň
    # predictions = np.argmax(scores_matrix, axis=1)  # Index nejvyšší hodnoty v každém řádku
    # match_counts = np.max(scores_matrix, axis=1)
    
    # # for each prediction get time offset
    # # predicted_time_offsets = time_offsets[np.arange(N_test), predictions]


    # # Porovnej s klíčem
    # correct_mask = (predictions == pred_key)
    # correct_predictions = predictions[correct_mask]

    # print(f"Correct predictions: {len(correct_predictions)} out of {N_valid}")
    # for i in range(N_valid):
    #     print(f"Validation song {i}: Predicted = {predictions[i]}, Actual = {pred_key[i]}, Matches = {match_counts[i]}")
    # incorrect_predictions = predictions[~correct_mask]
    # print(f"Incorrect predictions: {len(incorrect_predictions)} out of {N_valid}")
    # for i in range(N_valid):
    #     if predictions[i] != pred_key[i]:
    #         print(f"Validation song {i}: Predicted = {predictions[i]}, Actual = {pred_key[i]}, Matches = {match_counts[i]}")

    
    # song_id, matches, offset = recognize_signal_time_offset(valid_signals[15], fingerprint_db)
    # print(f"Matched song: {song_id}")
    # print(f"Matches: {matches}")
    # print(f"Query starts at position: {offset/100:.1f}s in the known song")

    # PHASE 8 test data with time offset
    # fingerprint_db = build_fingerprint_database(known_signals, load_from_file=LOAD_FROM_FILE, save_to_file=SAVE_TO_FILE, filename=FILE_NAME)
    # start_time = time.time()


