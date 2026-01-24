# ISS - Signals and Systems

Advanced course in digital signal processing and systems theory from BUT FIT (Brno University of Technology).

## Course Content

- **Mathematical Foundations** - Complex exponentials, mathematical preliminaries
- **Spectral Analysis** - Fourier Series, Fourier Transform, DFT, FFT
- **Digital Filtering** - FIR/IIR filter design and implementation, C implementations
- **Random Processes** - Stochastic signals, statistical signal processing
- **Image Processing** - 2D signal processing and transforms
- **Continuous Systems** - Continuous-time Fourier Series and Transform
- **System Analysis** - Laplace Transform, frequency response, transfer functions
- **Sampling Theory** - Nyquist-Shannon theorem, sample rate conversion

## Requirements

Python 3.8+ with dependencies in `requirements.txt`:

```
matplotlib>=3.7.0
numpy>=1.24.0
jupyter>=1.0.0
soundfile
scipy
tqdm
```

## Setup

Windows:
```powershell
.\setup_env.ps1
.\activate.ps1
jupyter notebook
```

Linux/macOS:
```bash
source setup.bash
pip install -r requirements.txt
jupyter notebook
```

## Repository Structure

- `00-11_*/` - Weekly lab exercises
- `ex/` - Additional exercises
- `proj/` - Course project
- `pulsem/` - Midterm exams
- `zk/` - Final exams
- `04_filtering_1/c/` - C filter implementations

## Topics Covered

**Transform Theory:** Fourier Series/Transform (continuous/discrete), Z-Transform, Laplace Transform, STFT

**Signal Processing:** Convolution, correlation, filtering, spectral analysis, sampling, noise analysis

**Implementation:** NumPy, SciPy, real-time processing, audio processing, performance optimization
