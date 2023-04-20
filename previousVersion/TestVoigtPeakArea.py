import numpy as np
from scipy import special, optimize, integrate
from matplotlib import pyplot as plt

def voigt(x, *params):
    num_V = len(params)

    y_V = np.zeros_like(x)
    for i in range(num_V):
        BE = params[i][0]
        I = params[i][1]
        W_G = params[i][2]
        gamma = params[i][3]
        SOS = params[i][4]
        BR = params[i][5]

        z = (x - BE + 1j*gamma)/((W_G/BR) * np.sqrt(2.0)) # 強度の大きいピークに対する複素変数の定義
        w = special.wofz(z) #Faddeeva function (強度の大きい方)
        V_w = I * BR * (w.real)/((W_G/BR) * np.sqrt(2.0*np.pi))
        #V_w = I * BR * (w.real)

        y_V = y_V + V_w
        Area_Vw = integrate.trapz(V_w, x)

    return y_V, Area_Vw

#guess_WG = np.arange(0.3, 1.0, 0.3)
guess_WG = np.array([0.3, 0.6, 0.3*3/2, 0.4])
ratio = np.array([1, 0.5, 2/3, 0.75])

for i in range(len(guess_WG)):
    guess_G = [425, 1, guess_WG[i], 0.2, 0, 1]
    guess_BR = [425, 1, 0.3, 0.2, 0, ratio[i]]
    guess_GandBR = [425, 1, guess_WG[i], 0.2, 0, ratio[i]]
    #guess_L = [425, 1, 0.2, guess_WL[i], 0, 1]
    x = np.arange(300, 550, 0.1)
    
    V_xg = voigt(x, guess_G)
    V_xb = voigt(x, guess_BR)
    V_xgb = voigt(x, guess_GandBR)

    plt.plot(x, V_xg[0], label = f"WG={guess_WG[i]}")
    plt.plot(x, V_xb[0], label = f"BR={ratio[i]}")
    plt.plot(x, V_xgb[0], label = f"WG={guess_WG[i]}, BR={ratio[i]}")
    print(f"Area of Voigt function: (V_xg, V_xb ,V_xgb)={V_xg[1], V_xb[1] ,V_xgb[1]}")

plt.legend()
plt.show()