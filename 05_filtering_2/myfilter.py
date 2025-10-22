# Petr Palka 2021/22, fixes by Honza Cernocky 10/2022
#   fixed computation of the z-transform in complex plane. 
#   fixing colors of vectors - numerator blue, denominator red.
#   removing spectrogram - no need of sound3 anymore. 

import numpy as np
import matplotlib.pyplot as plt

from matplotlib import cm
from matplotlib.ticker import MaxNLocator

import matplotlib.colors
import matplotlib as mpl

# from sound3 import plot_spectrogram

# remove:
# import soundfile as sf
# from tkinter import font
# from matplotlib import gridspec
# from tkinter import font


cm_mag = cm.gist_rainbow #cm.hsv # cm.inferno # cm.magma
cm_angle = cm.hsv  # cm.twilight  

cm_mag_alpha = 0.65 # 0.75
cm_angle_alpha = 0.65 # 0.8

COLOR = 'k'
#mpl.rcParams['text.color'] = COLOR
#mpl.rcParams['axes.labelcolor'] = COLOR
#mpl.rcParams['xtick.color'] = COLOR
#mpl.rcParams['ytick.color'] = COLOR

fontsize=16
zp_color = '#233838'

from scipy.signal import spectrogram, lfilter, freqz, tf2zpk
from IPython.display import Markdown as md 
from IPython.display import display

class myFilter:
    
    def __init__(self, b, a, N=32, fs=44100, s=[]):
        self.b, self.a = b, a

        self.w, self.H = freqz(b, a)
        self.z, self.p, self.k = tf2zpk(b, a)

        self.N = N
        self.h = lfilter(b, a, self.unit_impulse(N))
        self.fs = fs
        self.signal = s

        # ['#21ad47', '#33a8d6', '#e0785e', '#e0a85e'] 
        self.angle_colors_p = ['#547A1D', '#6BA32D', '#96CC39', '#A7E074', '#C0EC83']
        #['#C0EC83', '#A7E074', '#96CC39', '#6BA32D', '#547A1D', '#3B5C0A']
        self.angle_colors_n = ['#C23210', '#D85F59', '#FF8A83', '#FFD0C2']
        #['#FFD0C2', '#FF8A83', '#D85F59',  '#C23210', '#9911D1']

    @staticmethod
    def unit_impulse(length):
        return [1, *np.zeros(length - 1)]
    
    def is_stable(self):
        return (self.p.size == 0) or np.all(np.abs(self.p) < 1)
    
    def filter_signal(self, s):
        return lfilter(self.b, self.a, s)

    
    def signal_spectogram(self, s):
        signal_f = self.filter_signal(s)
        f, t, sgr = spectrogram(signal_f, self.fs)
        sgr_log = 10 * np.log10(sgr+1e-20)
        return {"time": t, "freq": f, "sgr_log": sgr_log}
    
    def markdown_stable(self):
        display(md('Filter {} stable.'.format('$is$' if self.is_stable() else '$is\ not$')))
    
    def coef(self, arr, i):
        return (str(arr[i])+"e^{-j\omega"+str(i)+"}" if arr[i] else '')
     
    def markdown_eq(self):
        b, a = self.b, self.a
        B = [(self.coef(b, i) if i != 0 else str(b[i])) for i in range(len(b))]
        A = [(self.coef(a, i) if i != 0 else "1") for i in range(len(a))]
        while '' in B:
            B.remove('')
        while '' in A:
            A.remove('')
        if len(B) == 0:
            B.append(1)
        # changed $$ -> $
        eq = "$H(e^{j\omega}) = \\frac{"+' + '.join(B)+"}{"+' + '.join(A)+"}$"
        while '+ -' in eq:
            eq = eq.replace('+ -', '-')
        return eq
        #display(md(eq))

    def analysis(self, s):
        self.markdown_eq()
        self.markdown_stable()
        self.plot_ir()
        #self.plot_freq()
        #self.plot_complex()

        plt.tight_layout()
        #print(len(self.signal_spectogram(s)['sgr_log']))
        #plot_spectrogram(**self.signal_spectogram(s))  # todo

    def plot_ir(self, N=None):
        if N:
            self.N = N
            self.h = lfilter(self.b, self.a, self.unit_impulse(N)) 
        plt.figure(figsize=(10, 3))

        plt.stem(np.arange(self.N), self.h, basefmt=' ')

        plt.gca().set_xlabel('$n$')
        plt.gca().set_title('Impulse response $h[n]$')

        plt.grid(alpha=0.6, linestyle='--')
        plt.tight_layout()


    def plot_freq(self):  # fs global todo:...
        # TODO:
        _, ax = plt.subplots(1, 2, figsize=(14, 5))

        ax[0].plot(self.w / 2 / np.pi * self.fs, np.abs(self.H))
        ax[0].set_xlabel('Frequency [Hz]')
        ax[0].set_title('Magnitude response $|H(e^{j\omega})|$')

        ax[1].plot(self.w / 2 / np.pi * self.fs, np.angle(self.H))
        ax[1].set_xlabel('Frequency [Hz]')
        ax[1].set_title('Phase response $\mathrm{arg}\ H(e^{j\omega})$')

        for ax1 in ax:
            ax1.grid(alpha=0.5, linestyle='--')
        plt.tight_layout()


    def plot_complex(self, omega=0):
        """ Plots zeros & poles in complex plane with unit circle. """
        f = plt.figure(figsize=(8, 8))

        # jednotkova kruznice
        ang = np.linspace(0, 2*np.pi, 100)
        plt.plot(np.cos(ang), np.sin(ang), linewidth=1.2, color='#bf9602')

        # nuly
        plt.scatter(np.real(self.z), np.imag(self.z), 
            marker='o', facecolors='none', edgecolors='r', label='zeros', s=100, linewidths=2)
        # poly
        plt.scatter(np.real(self.p), np.imag(self.p),
            marker='x', color='g', label='poles', s=100, linewidths=4)
        

        for i in range(len(self.p)):
            break
            plt.plot([np.real(self.p[i]), 0], [np.imag(self.p[i]), 0], '--')
            plt.gca().annotate('|'+str(round(abs(self.p[i]), 3))+'|', 
                (np.real(self.p[i])/2., np.imag(self.p[i])/2.-0.08), fontsize=14, 
                rotation=np.angle(self.p[i], deg=True))

        point = np.exp(-1j * omega)
        for i in range(len(self.z)):
            plt.plot([np.real(self.z[i]), np.real(point)], [np.imag(self.z[i]), np.imag(point)], '--')
        plt.scatter(np.real(point), np.imag(point),
            marker='.', color='black', label='$H(j*omega)$', s=100, linewidths=4)

        plt.gca().set_xlabel('Real part $\mathbb{R}\{$z$\}$')
        plt.gca().set_ylabel('Imaginary part $\mathbb{I}\{$z$\}$')

        plt.axis('square')
        plt.grid(alpha=0.5, linestyle='--')
        plt.legend(loc='upper right')

        #plt.tight_layout()

    @staticmethod
    def plot_angle_area(ax, angle, point, r=0.05, color='#21ad47', alpha=0.5):
        omega_deltas = np.linspace(0, angle, 40, endpoint=True)
        x = np.concatenate((np.cos(omega_deltas), [1]) , axis=None)
        y = np.concatenate((np.sin(omega_deltas), [0]) , axis=None)
  
        # Area above triangle
        ax.fill_between(r*x+point.real, r*y+point.imag, 
            color=color, alpha=alpha, linewidth=0)
        # Triangle
        ax.fill_between(  # TODO: ... use complex, not numpy.complex128 //arr
            [0, r*np.cos(angle), r*1]+point.real,
            [0, r*np.sin(angle), 0]+point.imag, 
            [point.imag, point.imag, point.imag],
            color=color, alpha=alpha, linewidth=0)

    fontsize=18
    def plot_zplane_mod(self, ax, omega):
        """ Complex plane - modul of z. """
        ax.set_xlabel('$\mathfrak{Re}(z)$', fontsize=fontsize+2)
        ax.set_ylabel('$\mathfrak{Im}(z)$', fontsize=fontsize+2, labelpad=-10)
        ax.set_xlim(-1.15, 1.15) 
        ax.set_ylim(-1.15, 1.15)
        ax.axis('square')
        ax.set_title('mod($z$)', pad=60, fontsize=14)

        # np.polyval order: x^n, x^n-1, ..., x^0 - honza correcting - should not reverse.  
        #b = list(reversed(self.b))  
        #a = list(reversed(self.a))
        a = self.a 
        b = self.b 
        
        step = 0.01
        X = np.arange(-1.25, 1.25 + step, step)
        X, Y = np.meshgrid(X, X)
        #Z = np.polyval(b, X + Y*1j) / np.polyval(a, X + Y*1j)    # honza correction ? not z^n, but z^{-n} !!
        Z = np.polyval(b, X - Y*1j) / np.polyval(a, X - Y*1j)  
        
        pcm = ax.pcolormesh(
            X, Y, np.abs(Z), 
            vmin=0, # np.min(np.abs(Z)),
            vmax=min(20, np.max(np.abs(Z))), # cut
            cmap=cm_mag, 
            alpha=cm_mag_alpha)
        plt.colorbar(pcm, ax=ax, orientation='horizontal', 
                     fraction=0.046, pad=0.04, location='top')
                     
        ejo = np.exp(1j * omega)
        self.plot_points(ax, ejo)
        ax.grid(alpha=0.9, linestyle='--', color='#333333')
         
        
    def plot_points(self, ax, ejo):
        # Unit circle
        ang = np.linspace(0, 2*np.pi, 180) 
        ax.plot(np.cos(ang), np.sin(ang), linestyle='-', linewidth=1.2, color='k')

        # zeros
        ax.scatter(self.z.real, self.z.imag, marker='o', facecolors='none',
            edgecolors=zp_color, label='zeros', s=150, linewidths=4)
        # poles
        ax.scatter(self.p.real, self.p.imag, marker='x', color=zp_color, 
            label='poles', s=150, linewidths=5)
        # cexp omega ejo
        ax.scatter(ejo.real, ejo.imag, marker='.', color='k', s=100, linewidths=4,
            label='$H(e^{j \omega})$')

    def plot_zplane(self, ax, omega):
        """ Z-plane """
        ax.set_xlabel('$\mathfrak{Re}(z)$', fontsize=fontsize+2)
        ax.set_ylabel('$\mathfrak{Im}(z)$', fontsize=fontsize+2, labelpad=-10)
        ax.set_xlim(-1.15, 1.15) 
        ax.set_ylim(-1.15, 1.15)
        ax.axis('square')
        ax.grid(alpha=0.9, linestyle='--', color='#333333')
        ax.set_title('moduls & arguments ', pad=55, fontsize=14)

        # Unit circle
        ang = np.linspace(0, 2*np.pi, 180) 
        ax.plot(np.cos(ang), np.sin(ang), linestyle='-', linewidth=1.2, color='k') 

        ejo = np.exp(1j * omega)
        color = ('r' if omega < 0 else 'g')
        self.plot_angle_area(ax, np.angle(ejo), 0*ejo, r=1, color=color, alpha=0.05)
               
        # Plots lines and angles between e^jo and zeros/poles 
        r = 0.2  # radius of semicircle representing angle
        for z in self.z:
            ax.plot(np.real([z, ejo]), np.imag([z, ejo]), '-', color='b')  # honza fix
            vec = ejo - z
            #color = 'g' if np.angle(vec) >= 0 else 'r'
            myFilter.plot_angle_area(ax, np.angle(vec), z, r=r, color='b')

        for p in self.p:
            ax.plot(np.real([p, ejo]), np.imag([p, ejo]), '-', color='r')   # honza fix 
            vec = ejo - p
            #color = 'g' if np.angle(vec) <= 0 else 'r'
            myFilter.plot_angle_area(ax, np.angle(vec), p, r=r, color='r')

        # Plot ejo, zeros and poles:
        self.plot_points(ax, ejo)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15),
          ncol=3, fancybox=True, shadow=True, fontsize=14)

        # creates empty space (padding) instead of colorbar
        plt.colorbar(
            matplotlib.cm.ScalarMappable(), ax=ax,    
            orientation='horizontal', location='top', 
            fraction=0.046, pad=0.04
        ).remove()
            
    def demo(self, omega=0, symmetry=False):
        fig = plt.figure(figsize=(20, 12))  # 16, 14  # 12, 10

        # Equation:
        fig.suptitle(self.markdown_eq(), fontsize=fontsize+8, y=1.05)

        ax_blank = plt.subplot2grid((4, 3), (0, 0), rowspan=2, colspan=1)
        ax0 = plt.subplot2grid((4, 3), (0, 1), rowspan=2, colspan=1)
        ax3 = plt.subplot2grid((4, 3), (0, 2), rowspan=2, colspan=1)

        ax_mag = plt.subplot2grid((4, 3), (2, 0), colspan=3)
        ax_ang = plt.subplot2grid((4, 3), (3, 0), colspan=3)
        
        fig.subplots_adjust(left=0.1, right=0.9,
                            bottom=0.1, top=0.9,
                            hspace=0.5, wspace=0.15)
        # Complex planes:
        self.plot_zplane(ax_blank, omega)
        self.plot_zplane_mod(ax0, omega)  # left
        self.plot_zplane_ang(ax3, omega)  # right
        
        # Magnitude response
        ax_mag.set_title('Magnitude response: $|H(e^{j\omega})|$', fontsize=fontsize)
        ax_mag.plot(self.w, np.abs(self.H), color='k')  # / 2 / np.pi * self.fs
        if symmetry:
            ax_mag.plot(-self.w, np.abs(self.H), color='k')
        else:
            ax_mag.set_xlim(0, np.pi)  # MAG
        
            #ax1.set_xticks(np.linspace(-np.pi, np.pi, 7))  # if
        #else:
        #    ax1.set_xticks(np.linspace(0, np.pi, 7))

        ax_mag.grid(linestyle='--')
        ax_mag.yaxis.set_major_locator(MaxNLocator(5))
        ax_mag.spines['bottom'].set_position('zero')
        
        #ax1.set_xlabel('$\omega$ rad')

        index = round((len(self.H)-1)*abs(omega)/np.pi)
        Y = abs(self.H[index])
        ax_mag.plot([omega, omega],[0, Y], 'k', linewidth=0.7)
        ax_mag.scatter(omega, Y, marker='.', color='k', s=100, linewidths=4, zorder=10)
         
        #############################################################
        X = np.linspace(-1.25, 1.25, 250, endpoint=True)
        Y = np.linspace(-1.25, 1.25, 250, endpoint=True)

        X, Y = np.meshgrid(X, Y)
        
        # Calculate complex values inside plot plane 
        b = list(reversed(self.b))  
        a = list(reversed(self.a))

        step = 0.01
        X = np.arange(-1.25, 1.25 + step, step)
        Y = np.arange(-1.25, 1.25 + step, step)

        X, Y = np.meshgrid(X, Y)
        Z = np.polyval(b, X + Y*1j) / np.polyval(a, X + Y*1j)    # honza correction here ? 
        maxx = min(50, np.max(np.abs(Z)))
        

        X = np.linspace(-np.pi, np.pi, 400)
        Y = np.linspace(0, 11/10*max(abs(self.H)), 50, endpoint=True)
        X, Y = np.meshgrid(X, Y)

        hindex = np.rint((len(self.H)-1)*abs(X)/np.pi).astype('int')
        Z = np.abs(self.H[hindex])
        
        #pcm = ax_mag.pcolormesh(X, Y, Z,    # honza does not want 
        #    vmin=0, 
        #    vmax=maxx, 
        #    cmap=cm_mag, 
        #    alpha=cm_mag_alpha)
        
        # LEFT
        X = np.linspace(-np.pi, 0, 200, endpoint=False)
        Y = np.linspace(-np.pi, np.pi, 50)
        X, Y = np.meshgrid(X, Y)
        hindex = np.rint((len(self.H)-1)*abs(X)/np.pi).astype('int')
        Z = -np.angle(self.H[hindex])
        #pcm = ax_ang.pcolormesh(             # honza does not want 
        #    X, Y, Z, 
        #    vmin=-np.pi, 
        #    vmax=np.pi, 
        #    cmap=cm_angle, 
        #    alpha=cm_angle_alpha)  
        
        # RIGHT
        X = np.linspace(0, np.pi, 200)
        Y = np.linspace(-np.pi, np.pi, 50)
        X, Y = np.meshgrid(X, Y)
        hindex = np.rint((len(self.H)-1)*abs(X)/np.pi).astype('int')
        Z = np.angle(self.H[hindex])
        #pcm = ax_ang.pcolormesh(             # honza does not want 
        #    X, Y, Z, 
        #    vmin=-np.pi, 
        #    vmax=np.pi, 
        #    cmap=cm_angle, 
        #    alpha=cm_angle_alpha)
        
        ####################################################
        ax_mag.tick_params(axis='x', labelsize=0, colors='#ffffff')
        ax_mag.tick_params(axis='y', labelsize=16)
    
        
        # Phase response
        ax_ang.sharex(ax_mag)  # matplotlib >= 3.3.4
        ax_ang.tick_params(axis='both', labelsize=16)
        
        ax_ang.set_title('Phase response: $\mathrm{arg}\ H(e^{j\omega})$', 
            fontsize=fontsize)
        ax_ang.plot(self.w, np.angle(self.H), color='k')
        
        ax_ang.set_xlabel('$\omega$ rad', fontsize=fontsize)
        ax_ang.set_ylim((-np.pi, np.pi))
        
        Y = np.sign(omega)*np.angle(self.H[index])
        ax_ang.plot([omega, omega],[0, Y], 'k', linewidth=0.9)
        ax_ang.scatter(omega, Y, marker='.', color='k', s=100, linewidths=4)

        ax_ang.grid(linestyle='--', alpha=0.6, color='k')
        if symmetry:
            ax_ang.plot(-self.w, -np.angle(self.H), color='k')
            
            ax_ang.set_xticks(np.linspace(-np.pi, np.pi, 17))
            ax_ang.set_xticklabels((
                '$-\pi$',
                '$-\\frac{7\pi}{8}$', 
                '$-\\frac{3\pi}{4}$',
                '$-\\frac{5\pi}{8}$',
                '$-\\frac{\pi}{2}$',
                '$-\\frac{3\pi}{8}$',
                '$-\\frac{\pi}{4}$',
                '$-\\frac{\pi}{8}$',
                '0', 
                '$\\frac{\pi}{8}$',
                '$\\frac{\pi}{4}$',
                '$\\frac{3\pi}{8}$',
                '$\\frac{\pi}{2}$',
                '$\\frac{5\pi}{8}$',
                '$\\frac{3\pi}{4}$',
                '$\\frac{7\pi}{8}$', 
                '$\pi$'
            ))
            
        else:
            ax_ang.set_xticks(np.linspace(0, np.pi, 9))
            ax_ang.set_xticklabels((
                '0', 
                '$\\frac{\pi}{8}$',
                '$\\frac{\pi}{4}$',
                '$\\frac{3\pi}{8}$',
                '$\\frac{\pi}{2}$',
                '$\\frac{5\pi}{8}$',
                '$\\frac{2\pi}{3}$',
                '$\\frac{7\pi}{8}$', 
                '$\pi$'
            ))
            ax_ang.set_xlim(0, np.pi)
    
        ax_ang.set_yticks(np.linspace(-np.pi, np.pi, 5))
        ax_ang.set_yticklabels((
            '$-\pi$', 
            '$-\\frac{\pi}{2}$', 
            '0', 
            '$ \\frac{\pi}{2}$', 
            '$ \pi$'
        ))
        # fig.tight_layout()


    def plot3d_zplane(self, ax0, omega=0):

        ang = np.linspace(0, 2*np.pi, 160)
        ax0.plot(np.cos(ang), np.sin(ang), linestyle='-', linewidth=1.2, color='k') # #bf9602
        ax0.grid(alpha=0.7, linestyle='--')

        point = np.exp(-1j * omega)
    

        # zeros
        ax0.scatter(np.real(self.z), np.imag(self.z), marker='o', 
            facecolors='none', edgecolors='r', label='zeros', s=150, linewidths=2)
        # poles
        ax0.scatter(np.real(self.p), np.imag(self.p),
            marker='x', color='g', label='poles', s=150, linewidths=4)

        # cexp omega point
        ax0.scatter(np.real(point), np.imag(point), marker='.', color='black', 
            label='$H(e^{j \omega})$', s=100, linewidths=4)
        ax0.set_xlabel('$\mathfrak{Re}(z)$', fontsize=fontsize+2)
        ax0.set_ylabel('$\mathfrak{Im}(z)$', fontsize=fontsize+2, rotation=0, labelpad=25)

 
        ax0.set_xlim(-1.15, 1.15) 
        ax0.set_ylim(-1.15, 1.15)

        b = list(reversed(self.b))  # np.polyval order: x^n, x^n-1, ..., x^0
        a = list(reversed(self.a))

        step = 0.025
        X = np.arange(-1.25, 1.25 + step, step)
        Y = np.arange(-1.25, 1.25 + step, step)

        X, Y = np.meshgrid(X, Y)

        Z = np.polyval(b, (X + Y*1j)) / np.polyval(a, (X + Y*1j))
        zlim = 20
        #Z[abs(Z.real) > zlim] = np.nan + 0.j
        
        # Plot the surface.
        surf = ax0.plot_surface(X, Y, np.angle(Z), cmap=cm.hsv, 
            linewidth=0, antialiased=True, alpha=0.65,
            vmin=-np.pi/2, vmax=np.pi/2)
                            
         # vmin=-np.max(abs(Z))/2, vmax=np.max(abs(Z))/2)
         
        ax0.set_zlim(-6, 6)  # ax.set_zlim3d(-500, 500)
        plt.colorbar(surf, shrink=0.6, aspect=10, ax=ax0)

        ax0.view_init(elev=90, azim=-90)
        # ax.axis('off')
        ax0.set_zticks([])

        
    def plot_zplane_ang(self, ax0, omega):
        # Plane:
        ax0.set_title('arg($z$)', pad=60, fontsize=14)
        ax0.set_xlabel('$\mathfrak{Re}(z)$', fontsize=fontsize+2)
        ax0.set_ylabel('$\mathfrak{Im}(z)$', fontsize=fontsize+2, labelpad=-10)                   
        ax0.set_xlim(-1.15, 1.15) 
        ax0.set_ylim(-1.15, 1.15)
        ax0.axis('square')

        # np.polyval order: x^n, x^n-1, ..., x^0
        b = [1, 0] #list(reversed(self.b))  
        a = [1] #list(reversed(self.a))


        X = np.linspace(-1.25, 1.25, 250, endpoint=True)
        Y = X
        X, Y = np.meshgrid(X, Y)

        result = ''.join(['(z {0.real:+0.2f} {0.imag:+0.2f}i)'.format(z) for z in self.z])

        # Calculate complex values inside plot plane 
        Z = 1 + 0j  # X + Y*1j - self.z[0]
        for z in self.z:
            Z *= X + Y*1j - z
        for p in self.p:
            Z /= X + Y*1j - p
        #print(type(np.complex(self.z[0])), type(np.complex(self.p[0])))
        #Z = np.polyval(b, X + Y*1j) / np.polyval(a, X + Y*1j)
    
        pcm = ax0.pcolormesh(X, Y, np.angle(Z), 
            vmin=-np.pi, 
            vmax=+np.pi, 
            cmap=cm_angle, 
            alpha=cm_angle_alpha)
        cbar = plt.colorbar(pcm, ax=ax0, 
            orientation='horizontal', 
            location='top',
            fraction=0.046, pad=0.04, 
            ticks=np.linspace(-np.pi, np.pi, 8+1, endpoint=True))
        
        radian = False
        if radian:
            cbar.ax.set_xticklabels([
                '$-\pi$',
                '$-\\frac{3\pi}{4}$',
                '$-\\frac{\pi}{2}$',
                '$-\\frac{\pi}{4}$',
                '0', 
                '$\\frac{\pi}{4}$',
                '$\\frac{\pi}{2}$',
                '$\\frac{3\pi}{4}$',
                '$\pi$'
            ], fontsize=14)
        else:
            cbar.ax.set_xticklabels([
                '$-180°$',
                '$-135°$',
                '$-90°$',
                '$-45°$',
                '$0°$', 
                '$45°$',
                '$90°$',
                '$135°$',
                '$180°$',
            ])     
        #####################################

        # Unit circle
        ang = np.linspace(0, 2*np.pi, 200)
        ax0.plot(np.cos(ang), np.sin(ang), linestyle='-', linewidth=1.4, color='k')
        ax0.grid(alpha=0.6, linestyle='--', linewidth=1.2, color='#333333')

        # zeros
        ax0.scatter(np.real(self.z), np.imag(self.z), marker='o', 
            facecolors='none', edgecolors=zp_color, label='zeros', s=150, linewidths=4)
        # poles
        ax0.scatter(np.real(self.p), np.imag(self.p),
            marker='x', color=zp_color, label='poles', s=150, linewidths=5)

        # complex exp omega point (ejo)
        ejo = np.exp(1j * omega)
        ax0.scatter(np.real(ejo), np.imag(ejo), marker='.', color='black', 
            label='$H(e^{j \omega})$', s=100, linewidths=4)

