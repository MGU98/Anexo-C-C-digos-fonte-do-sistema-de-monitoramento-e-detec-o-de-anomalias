
import pandas as pd
import numpy as np
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import librosa
import librosa.display
from scipy.signal import get_window

# === 1. Carregar os dados ===
filename = "logs/classifications.csv"
data = pd.read_csv(filename)

# === 2. Selecionar as features relevantes ===
features = ["x", "y", "z", "current"]
X = data[features]

# === 3. Aplicar scaling (MinMax entre 0 e 1) ===
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# === 4. Treinar o modelo One-Class SVM ===
model = OneClassSVM(kernel="rbf", gamma=0.1, nu=0.01)  # nu ≈ % de anomalias esperadas
model.fit(X_scaled)

# === 5. Prever anomalias nos dados existentes ===
predictions = model.predict(X_scaled)  # 1 = normal, -1 = anomalia
data["predicted_anomaly"] = predictions
data["predicted_anomaly"] = data["predicted_anomaly"].map({1: False, -1: True})

# === 6. Visualização das detecções ===
plt.figure(figsize=(6, 4))
sns.countplot(x=data["predicted_anomaly"])
plt.title("Detecção de Anomalias com One-Class SVM")
plt.xticks([0, 1], ["Normal", "Anomalia"])
plt.xlabel("Classe Prevista")
plt.ylabel("Número de Amostras")
plt.tight_layout()
plt.savefig("logs/grafico_1.png")

# === 6A. Gráfico de sinais no tempo ===
SAMPLE_RATE = 200  # Hz
SAMPLE_TIME = len(data) / SAMPLE_RATE
time = np.linspace(0, SAMPLE_TIME, len(data))

fig, axs = plt.subplots(4, 1, figsize=(12, 10))
fig.suptitle("Sinais no Domínio do Tempo", fontsize=14)
for i, col in enumerate(features):
    axs[i].plot(time, data[col], label=col)
    axs[i].set_ylabel("Amplitude")
    axs[i].set_title(col)
    axs[i].grid(True, alpha=0.3)
axs[-1].set_xlabel("Tempo (s)")
plt.tight_layout()
plt.savefig("logs/grafico_2.png")

# === 6B. Gráfico de FFT (espectro de frequência) ===
hann = get_window("hann", len(data))
freqs = np.fft.rfftfreq(len(data), d=1/SAMPLE_RATE)
fig, axs = plt.subplots(4, 1, figsize=(12, 10))
fig.suptitle("FFT por Canal", fontsize=14)

for i, col in enumerate(features):
    signal = data[col].values - np.mean(data[col].values)
    fft = np.abs(np.fft.rfft(signal * hann))
    axs[i].plot(freqs[1:], fft[1:])
    axs[i].set_title(f"FFT - {col}")
    axs[i].set_ylabel("Amplitude")
    axs[i].grid(True, alpha=0.3)
axs[-1].set_xlabel("Frequência (Hz)")
plt.tight_layout()
plt.savefig("logs/grafico_3.png")

# === 6C. Espectrograma usando Librosa ===
for i, col in enumerate(features):
    signal = data[col].values - np.mean(data[col].values)
    fig, ax = plt.subplots(figsize=(10, 4))
    S = librosa.stft(signal, n_fft=128, hop_length=64)
    S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
    img = librosa.display.specshow(S_db, sr=SAMPLE_RATE, hop_length=64,
                                   x_axis='time', y_axis='hz', ax=ax)
    ax.set_title(f"Espectrograma - {col}")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.tight_layout()
    plt.savefig(f"logs/grafico_4-{i}.png")

# === 7. Salvar modelo e scaler ===
joblib.dump(model, "oneclass_svm_model.pkl")
joblib.dump(scaler, "scaler.pkl")
print("Modelo salvo em 'oneclass_svm_model.pkl'")
print("Scaler salvo em 'scaler.pkl'")

# === 8. Estatísticas finais ===
print("\nResumo das previsões:")
print(data["predicted_anomaly"].value_counts())
print("\nPrévia dos dados com anomalia prevista:")
print(data.head())
