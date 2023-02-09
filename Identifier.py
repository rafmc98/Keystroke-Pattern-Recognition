import torch
import time
import json
import os
import math
from csv import DictWriter
from KeyboardListener import KeyboardListener


class Identifier:

    def __init__(self):
        self.template_number = 1
        self.input_word = "il futuro è passato di qui"
        self.classes = {}
        self.sample = {}
        self.feat_to_idx = {"hold_1": 0, "press_press": 1, "release_press": 2,
                            "release_release": 3, "hold_2": 4, "total_time": 5,
                            "slope_h1": 6, "slope_pp": 7, "slope_rp": 8,
                            "slope_rr": 9, "slope_h2": 10, "slope_tt": 11
                            }

    def dict_to_tensor(self, data):
        tot_tensor = torch.Tensor(len(data), 12)
        for digram in data:
            int_digram = int(digram)
            for feature in data[digram]:
                feat = self.feat_to_idx[feature]
                tot_tensor[int_digram][feat] = data[digram][feature]
        return tot_tensor

    def gaussian_likelihood(self, sample, mean, std):
        """
            Gaussian likelihood
            X: A torch tensor for the data.
            mean: A float for the mean of the gaussian.
            std: A float for the standard deviation of the gaussian.
        """
        raw_like = 1/((2*math.pi*std)**0.5) * \
            torch.exp(-(sample - mean)**2/(2*std))
        dummy = torch.tensor(0.01)
        dummy_t = dummy.repeat(len(sample), 12)
        like = torch.nan_to_num(raw_like, nan=0)
        adjusted = torch.maximum(like, dummy_t)
        return torch.log(adjusted)

    def get_classes(self):
        """
            Extracts tensors from the passphrase dataset
        """
        directory = "dataset/passphrase"
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            username = filename.split('.')[0]
            with open(f) as json_file:
                data_list = json.load(json_file)
                tensor_sequence = []
                for template in data_list:
                    tensor_sequence.append(self.dict_to_tensor(template))
                self.classes[username] = torch.stack(tensor_sequence)

    def find_minimum_distances(self, data, claim):
        differences = torch.min(torch.abs(data - claim), dim=0).values
        return differences

    def euclidean_distances(self, data, claim):
        distances = torch.abs(data - claim)
        norms = []
        for i in distances:
            norms.append(torch.norm(i))
        return min(norms)

    def compute_scores(self, sample):
        bayes_distances = {}
        norm_distances = {}
        print("{:<15} {:<20} {:<20}".format("USERNAME", "BAYES", "L2 NORM"))
        sums = {}
        norms = {}
        for user in self.classes:
            means = torch.mean(self.classes[user], 0)
            std = torch.std(self.classes[user], 0)
            user_score_tensor = self.gaussian_likelihood(sample, means, std)
            sums[user] = torch.sum(user_score_tensor)
            sums_score = torch.sum(
                user_score_tensor).item() / (len(self.input_word) - 1)

            differences = self.find_minimum_distances(
                self.classes[user], sample)
            norms[user] = torch.norm(differences)
            norm_score = norms[user].item() / (len(self.input_word) - 1)

            bayes_distances[user] = sums_score
            norm_distances[user] = norm_score
            print("{:<15} {:<20} {:<20}".format(user, sums_score, norm_score))

        max_value = max(sums, key=sums.get)
        print('\nBayes result:')
        print(max_value + ',', 'is that you?')

        print("\nL1 Norm results: ")
        min_value = min(norms, key=norms.get)
        print(min_value + ',', 'is that you?')

        print('PLEASE STOP RIGHT THERE!')
        typer = input("type your name, we need it! =) : ")
        print(typer)

        field_names = ["username", "predicted_user", "score"]
        with open('results/identification_bayes.csv', 'a') as bayes_csv:
            data = {'username': typer, 'predicted_user': max_value,
                    'score': sums[max_value].item()}
            writer_object = DictWriter(bayes_csv, fieldnames=field_names)
            writer_object.writerow(data)
            bayes_csv.close()

        with open('results/identification_norm.csv', 'a') as norm_csv:
            data = {'username': typer, 'predicted_user': min_value,
                    'score': norms[min_value].item() / (len(self.input_word) - 1)}
            writer_object = DictWriter(norm_csv, fieldnames=field_names)
            writer_object.writerow(data)
            norm_csv.close()

        field_names = ["username", "alessandro", "barbara", "ciro", "giovanna", "lavi",
                       "livia", "luca", "mara", "marco", "maurizio", "pietro", "rluzist1",
                       "shadow2030", "tommaso"]
        with open('results/identification_bayes_all_vs_all.csv', 'a') as bayes_csv_all_vs_all:
            data = {'username': typer}
            for username in bayes_distances.keys():
                data[username] = bayes_distances[username]
            print(data)
            writer_object = DictWriter(bayes_csv_all_vs_all, fieldnames=field_names)
            writer_object.writerow(data)
            bayes_csv_all_vs_all.close()

        with open('results/identification_norm_all_vs_all.csv', 'a') as norm_csv_all_vs_all:
            data = {'username': typer}
            for username in norm_distances.keys():
                data[username] = norm_distances[username]
            print(data)
            writer_object = DictWriter(norm_csv_all_vs_all, fieldnames=field_names)
            writer_object.writerow(data)
            norm_csv_all_vs_all.close()

    def start_identification(self):
        listener = KeyboardListener(self.input_word, self.template_number, "identification")
        listener.start_listener()

        self.get_classes()
        probe_tensor = self.dict_to_tensor(listener.probe_list[0])

        self.compute_scores(probe_tensor)


if __name__ == '__main__':
    identifier = Identifier()
    identifier.start_identification()
