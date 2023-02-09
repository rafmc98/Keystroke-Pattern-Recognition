from KeyboardListener import KeyboardListener
import json
import os
import torch
import torch.nn as nn
from csv import DictWriter
import math


class Verifier:

    def __init__(self):
        self.username = input("type your username : ")
        self.input_word = input("type your password : ")
        self.template_number = 1
        self.feat_to_idx = {"hold_1": 0, "press_press": 1, "release_press": 2,
                            "release_release": 3, "hold_2": 4, "total_time": 5,
                            "slope_h1": 6, "slope_pp": 7, "slope_rp": 8,
                            "slope_rr": 9, "slope_h2": 10, "slope_tt": 11
                            }

    def check(self):
        user_list = [filename.split("_")[0]
                     for filename in os.listdir('dataset/password')]
        if self.username not in user_list:
            print('The user is not registered in our system')
            return False
        else:
            return True

    def extract_metrics(self, data):
        tot_tensor = torch.Tensor(8, len(data[0]), 12)
        for insertion_idx in range(0, len(data)):
            insertion = data[insertion_idx]
            for digram in insertion:
                for feature in insertion[digram]:
                    feat = self.feat_to_idx[feature]
                    tot_tensor[insertion_idx][int(
                        digram)][feat] = data[insertion_idx][digram][feature]
        return tot_tensor

    def dict_to_tensor(self, data):
        tot_tensor = torch.Tensor(len(data), 12)
        for digram in data:
            int_digram = int(digram)
            for feature in data[digram]:
                feat = self.feat_to_idx[feature]
                tot_tensor[int_digram][feat] = data[digram][feature]
        return tot_tensor


    def find_minimum_distances(self, data, claim):
        differences = torch.min(torch.abs(data - claim), dim=0).values
        return differences


    def euclidean_distances(self, data, claim):
        distances = torch.abs(data - claim)
        norms = []
        for i in distances:
            norms.append(torch.norm(i))
        return min(norms)


    def compute_norm(self, differences):
        return torch.norm(differences).item()


    def compute_logits(self, data, sample):
        means = torch.mean(data, 0)
        std = torch.std(data, 0)

        score_tensor = self.gaussian_likelihood(sample, means, std)
        return torch.sum(score_tensor).item()


    def gaussian_likelihood(self, sample, mean, std):
        raw_like = 1 / ((2 * math.pi * std) ** 0.5) * \
            torch.exp(-(sample - mean) ** 2 / (2 * std))
        dummy = torch.tensor(0.01)
        dummy_t = dummy.repeat(len(sample), 12)
        like = torch.nan_to_num(raw_like, nan=0)
        adjusted = torch.maximum(like, dummy_t)
        return torch.log(adjusted)

    def compare_metrics(self, probe):
        word = self.input_word.split(" ")
        word = "-".join(word)

        with open('dataset/password/' + self.username + '_' + word + '.json') as json_file:
            data_metrics = json.load(json_file)

        data_tensor = self.extract_metrics(data_metrics)
        probe_tensor = self.dict_to_tensor(probe)

        differences = self.find_minimum_distances(data_tensor, probe_tensor)

        print("{:<25} {:<10}".format('Naive Bayes score', 'L2 Norm score'))
        print("{:<25} {:<10}".format(self.compute_logits(data_tensor, probe_tensor) /
              (len(self.input_word) - 1), self.compute_norm(differences) / (len(self.input_word) - 1)))

        field_names = ["typer_user", "username", "score", "word_length"]
        typer_user = input(
            "Are you enrolled? if yes type your username, else type guest:  ")
        with open('results/verification_bayes.csv', 'a') as bayes_csv:
            data = {'typer_user': typer_user, 'username': self.username, 'score': self.compute_logits(
                data_tensor, probe_tensor) / (len(self.input_word) - 1), 'word_length': len(self.input_word)}
            writer_object = DictWriter(bayes_csv, fieldnames=field_names)
            writer_object.writerow(data)
            bayes_csv.close()

        with open('results/verification_norm.csv', 'a') as norm_csv:
            data = {'typer_user': typer_user, 'username': self.username, 'score': self.compute_norm(
                differences) / (len(self.input_word) - 1), 'word_length': len(self.input_word)}
            writer_object = DictWriter(norm_csv, fieldnames=field_names)
            writer_object.writerow(data)
            norm_csv.close()

    def start_verification(self):
        if not self.check():
            exit()
        listener = KeyboardListener(self.input_word, self.template_number)
        listener.start_listener()

        self.compare_metrics(listener.probe_list[0])


if __name__ == '__main__':
    verifier = Verifier()
    verifier.start_verification()
