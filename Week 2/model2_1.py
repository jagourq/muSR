import numpy as np
from numpy.linalg import eigh
from scipy.constants import hbar, mu_0
from matplotlib import pyplot as plt

def adj(a):
    return a.conj().T

def tp(*args):
    result = args[0]
    for t in args[1:]:
        result = np.kron(result, t)
    return result

FLUORINE_19_GYROMAGNETIC_RATIO = 251.662e6
MUON_GYROMAGNETIC_RATIO_OVER_2_PI = 136e6

I = np.eye(2)
sigma_x = np.array([
    [0, 1],
    [1, 0]
])
sigma_z = np.array([
    [1, 0],
    [0, -1]
])
S = (hbar/2)*np.array([
    [
        [0, 1],
        [1, 0]
    ],
    [
        [0, -1j],
        [1j, 0]
    ],
    [
        [1, 0],
        [0, -1],
    ]
])

class Model:
    def __init__(self, H, particle_count):
        self.energies, self.M = eigh(H)
        self.transition_amplitude_matrix = (
            2 * (np.abs(adj(self.M) @ tp(sigma_x, *[I]*(particle_count-1)) @ self.M)**2)
            + np.abs(adj(self.M) @ tp(sigma_z, *[I]*(particle_count-1)) @ self.M)**2
        ) / 3 / 2**particle_count
        self.rounded_frequencies = np.round(self.energies / hbar)
    
    def print_details(self):
        # S_muon = np.array([tp(s, I) for s in S])
        # S_fluorine = np.array([tp(I, s) for s in S])
        # J = (S_muon + S_fluorine) / hbar
        S_muon = np.array([tp(s, I, I) for s in S])
        S_fluorine1 = np.array([tp(I, s, I) for s in S])
        S_fluorine2 = np.array([tp(I, I, s) for s in S])
        J = (S_muon + S_fluorine1 + S_fluorine2) / hbar
        J2 = sum(J[i] @ J[i] for i in range(3))
        Jz = J[2]

        up_arrow = '\u2191'
        down_arrow = '\u2193'
        N = len(self.energies)
        particle_count = int(np.log2(len(self.energies)))
        for i in range(N):
            for j in range(particle_count-1, -1, -1):
                if i & (1 << j) == 0:
                    print(up_arrow, end='')
                else:
                    print(down_arrow, end='')
            print('|', end='')
        print()
        for i in range(N):
            for j in range(N):
                entry = self.M[j, i]
                if entry > 1e-8:
                    print('+'+' '*(particle_count-1), end='|')
                elif entry < -1e-8:
                    print('-'+' '*(particle_count-1), end='|')
                else:
                    print(' '*particle_count, end='|')
            # print(self.rounded_frequencies[i])
            print(
                f'j(j+1)={(adj(m.M[:, i]) @ J2 @ m.M[:, i]).real.round(2)}'
                f', jz={(adj(m.M[:, i]) @ Jz @ m.M[:, i]).real.round(2)}'
                f', E={self.rounded_frequencies[i]} Hz'
            )

    def polarisation(self, ts):
        N = len(self.energies)
        frequency_matrix = np.abs(np.tile(self.energies, (N, 1)).T - np.tile(self.energies, (N, 1))) / hbar
        return sum(
            self.transition_amplitude_matrix[i, j] * np.cos(frequency_matrix[i, j]*ts)
            for i in range(N) for j in range(N)
        )

    def plot_cosine_amplitudes(self, ax, colour=None):
        N = len(self.energies)
        frequency_matrix = np.abs(np.tile(self.energies, (N, 1)).T - np.tile(self.energies, (N, 1))) / hbar

        cos_amplitudes = {}

        for i in range(N):
            for j in range(N):
                cos_amplitudes[frequency_matrix[i, j].round()] = \
                    cos_amplitudes.get(frequency_matrix[i, j].round(), 0) + self.transition_amplitude_matrix[i, j]

        for (f, a) in cos_amplitudes.items():
            ax.axvline(f * 1e-6, 0, a, color=colour)

        ax.set_title('Cosine amplitudes')
        ax.set_xlabel('Frequency / $GHz$')
        ax.set_ylabel('Amplitude')

    def plot_energy_levels(self, ax, colour=None):
        N = len(self.energies)
        rounded_frequencies = np.round(self.energies / hbar)
        frequency_levels = set(rounded_frequencies)
        transitions = set()
        for i in range(N):
            for j in range(N):
                if self.transition_amplitude_matrix[i, j] > 1e-8:
                    a = rounded_frequencies[i]
                    b = rounded_frequencies[j]
                    if a > b:
                        a, b = b, a
                    if a != b:
                        transitions.add((a, b))
        for f in frequency_levels:
            ax.axhline(f/1e6, 0, len(transitions)+1, color=colour)
        x = 1
        for (a, b) in transitions:
            ax.annotate('', (x, a/1e6), (x, b/1e6), arrowprops={'arrowstyle': '<->'})
            x += 1
        ax.set_title('Muon spin energy levels')
        ax.set_xlim(0, len(transitions)+1)
        ax.set_ylabel('Frequency / $GHz$')
        ax.get_xaxis().set_visible(False)

compare = False

# DISTANCE = 0.06e-9
DISTANCE = 2.34e-10/2
C = (
    mu_0 *
    FLUORINE_19_GYROMAGNETIC_RATIO *
    MUON_GYROMAGNETIC_RATIO_OVER_2_PI / (2*DISTANCE**3)
)
C2 = (
    mu_0 *
    FLUORINE_19_GYROMAGNETIC_RATIO *
    FLUORINE_19_GYROMAGNETIC_RATIO / (4*np.pi*DISTANCE**3)
)

# m = Model(C*(
#     sum(tp(S[i], S[i]) for i in range(3)) - 3*tp(S[2], S[2])
# ), 2)

H = C*(
    sum(tp(S[i], S[i], I) for i in range(3)) - 3*tp(S[2], S[2], I)
    + sum(tp(S[i], I, S[i]) for i in range(3)) - 3*tp(S[2], I, S[2])
)
m = Model(H, 3)

m.print_details()

if compare:
    # m2 = Model(C*(
    #     sum(tp(S[i], S[i], I) for i in range(3)) - 3*tp(S[2], S[2], I)
    #     + sum(tp(S[i], I, S[i]) for i in range(3)) - 3*tp(S[2], I, S[2])
    # ), 3)
    m2 = Model(C*(
        sum(tp(S[i], S[i], I) for i in range(3)) - 3*tp(S[2], S[2], I)
        + sum(tp(S[i], I, S[i]) for i in range(3)) - 3*tp(S[2], I, S[2])
    ) + C2*(
        sum(tp(I, S[i], S[i]) for i in range(3)) - 3*tp(I, S[2], S[2])
    ) / 8, 3)
    m2.print_details()

ts = np.arange(0, 1e-5, 1e-8)
# ts = np.arange(0, 1e-4, 1e-7)
D = m.polarisation(ts)
plt.title('Muon spin polarisation')
plt.plot(ts, D)
if compare:
    plt.plot(ts, m2.polarisation(ts))
plt.xlabel('Time / $s^{-1}$')
plt.ylabel('Polarisation')

plt.figure()
m.plot_energy_levels(plt.gca())
if compare:
    plt.figure()
    m2.plot_energy_levels(plt.gca(), 'orange')

plt.figure()
m.plot_cosine_amplitudes(plt.gca())
if compare:
    m2.plot_cosine_amplitudes(plt.gca(), 'orange')

plt.show()