import sklearn
import torch
import librosa
import numpy as np
import time
import os
import tqdm
import soundfile as sf
import matplotlib.pyplot as plt

def spectral_features(y, sr):
    features = [None] * 7
    features[0] = librosa.feature.rms(y)
    features[1] = librosa.feature.zero_crossing_rate(y)
    # Spectral features
    S, phase = librosa.magphase(librosa.stft(y=y))
    # Compute all descriptors
    features[2] = librosa.feature.spectral_rolloff(S=S)
    features[3] = librosa.feature.spectral_flatness(S=S)
    features[4] = librosa.feature.spectral_bandwidth(S=S)
    features[5] = librosa.feature.spectral_centroid(S=S)
    features[6] = librosa.yin(y, 50, 5000, sr=sr)[np.newaxis, :]
    features = np.concatenate(features).transpose()
    features[np.isnan(features)] = 1
    features = features[:-1, :]
    return features


class NSF:
    # m_path = "/home/martin/Desktop/Impact-Synth-Hardware/code/models/model_nsf_sinc_ema_impacts_waveform_5.0.th"
    m_path = "/home/hime/Work/Neurorack/Impact-Synth-Hardware/code/models/model_nsf_sinc_ema_impacts_waveform_5.0.th"
    f_pass = 3

    def __init__(self):
        # Testing NSF
        print('Creating empty NSF')
        self._model = None
        self._wav_file = 'reference_impact.wav'

    def dummy_features(self, wav):
        y, sr = librosa.load(wav)
        features = spectral_features(y, sr)
        return features

    def preload(self):
        self._model = torch.load(self.m_path, map_location="cuda")
        self._model = self._model.cuda()
        print("loaded")
        # features = self.dummy_features(self._wav_file)
        # features = torch.tensor(features[:10, :]).unsqueeze(0).cuda().float()
        #for p in range(self.f_pass):
        #    print("pass")
        #    with torch.no_grad():
        #        self._model(features)

    def generate_random(self, length=200):
        print('Generating random length ' + str(length))
        features = [torch.randn(1, length, 1).cuda()] * 7
        with torch.no_grad():
            audio = self._model(features)
        return audio.squeeze().detach().cpu().numpy()

    def generate(self, features):
        # features = self.dummy_features(wav)
        # features = torch.tensor(features).unsqueeze(0).cuda().float()
        with torch.no_grad():
            audio = self._model(features)
        return audio.squeeze().detach().cpu().numpy()


if __name__ == '__main__':
    root_dir = "/home/hime/Work/dataset/impacts"
    wav_adresses = [files_names for files_names in os.listdir(root_dir) if
                    (files_names.endswith('.wav') or files_names.endswith('.mp3'))]
    model = NSF()
    model.preload()
    import scipy
    import time
    # win = scipy.signal.hann(1024)
    # for wav in wav_adresses:
    #     if (wav == 'Impact38.wav'):
    #         print('Yeaaaaah')
    #         y, sr = librosa.load(root_dir + '/' + wav)
    #         features = spectral_features(y, sr)
    #         print(features.shape)
    #         features = torch.tensor(features).unsqueeze(0).cuda().float()
    #         audio = model.generate(features)
    #         sf.write("tst_generate_full.wav", audio, sr)
    #         for n_points in [2, 4, 8, 16, 32, 64]:
    #             print(n_points)
    #             print(features.shape[1] // n_points)
    #             final_audio = []
    #             p_ratio = (features.shape[1] - 1) // n_points
    #             last_val = None
    #             for f in range(p_ratio):
    #                 s_p = f * n_points
    #                 cur_time = time.time()
    #                 cur_feats = features[:, s_p:(s_p+n_points+1), :]
    #                 cur_audio = model.generate(cur_feats)
    #                 if (last_val is not None):
    #                     cur_audio[:512] = (last_val * np.linspace(1, 0, 512)) + (cur_audio[:512] * np.linspace(0, 1, 512))
    #                 last_val = cur_audio[-512:]
    #                 cur_audio = cur_audio[:-512]
    #                 print(time.time() - cur_time)
    #                 final_audio.append(cur_audio)
    #             final_audio = np.concatenate(final_audio)
    #             sf.write("tst_generate_" + str(n_points) + ".wav", final_audio, sr)
    #         exit()
    # for wav in wav_adresses:
    wav_list = ['dce_synth_one_shot_bumper_G#min.wav', 'SH_FFX_123BPM_IMPACT_01.wav',
                'FF_ET_whoosh_hit_little.wav', 'Afro_FX_Oneshot_Impact_3.wav']
    feats = []
    for wav in wav_list:
        y, sr = librosa.load(root_dir + '/' + wav)
        features = spectral_features(y, sr)
        features = torch.tensor(features).unsqueeze(0).cuda().float()
        audio = model.generate(features)
        sf.write("generation_testing/" + str(wav) + ".wav", audio, sr)
        feats.append(features)
    x_a = feats[2]
    x_b = feats[3]
    # Run through alpha values
    interp = []
    n_steps = 11
    size = min(x_a.shape[1], x_b.shape[1])
    x_a = x_a[:, :size, :]
    x_b = x_b[:, :size, :]
    alpha_values = np.linspace(0, 1, n_steps)
    for i, alpha in enumerate(alpha_values):
        x_interp = (1 - alpha) * x_b + alpha * x_a
        x_interp = model.generate(x_interp)
        interp.append(x_interp)
        sf.write("generation_testing/interp_" + str(i) + ".wav", x_interp, sr)
        # Draw interpolation step by step
        # stack_interp = torch.cat(interp, dim=0)
        # # Draw stacked interpolation
        # stack_test = stack_interp.clone().cpu().detach().numpy()
        # # plt.figure(figsize=(20, 20))
        # n_interp = stack_interp.shape[0]
        # n_features = stack_interp.shape[1]
        # for i in range(n_interp):
        #     for j in range(n_features):
        #         plt.subplot(n_features, n_interp, ((j * n_interp) + i) + 1)
        #         plt.plot(stack_test[i, j, :])
        # # plt.tight_layout(True)
        # plt.title("Interpolation")
        # plt.savefig(args.figures_path + 'interpolation.png')
        # plt.close()



