from pynput import keyboard
import time
import json


class KeyboardListener:

    def __init__(self, word, template_number, operation=""):
        self.final_dict = {}
        self.total_index = 0
        self.word = word
        self.temp_word = ''
        self.word_len = len(self.word)
        self.press = [0] * len(self.word)
        self.release = [0] * len(self.word)
        self.probe_list = []
        self.template_number = template_number
        self.template_index = 0
        self.operation = operation

    def on_press(self, key):
        self.press[self.total_index] = time.time()

        if key == keyboard.Key.space:
            self.temp_word += ' '
        elif not hasattr(key, 'char'):
            print("\nThe word you typed is not correct, please try again")
            self.reset()
            return False
        else:
            self.temp_word += key.char

    def on_release(self, key):

        self.release[self.total_index] = time.time()
        self.total_index += 1
        if self.total_index == self.word_len:
            if self.temp_word != self.word:
                print("\nThe word you typed is not correct, please try again")
            else:
                self.template_index += 1
                self.update_data()
            self.reset()
            return False

    def reset(self):
        self.total_index = 0
        self.press = [0] * len(self.word)
        self.release = [0] * len(self.word)
        self.temp_word = ''

    def update_data(self):
        press_press = []
        hold_1 = []
        hold_2 = []

        for index, value in enumerate(self.press):
            if value == 0:
                self.press[index] = self.release[index - 1]

        for index, (press, release) in enumerate(zip(self.press, self.release)):
            if index == 0:
                hold_1.append(release - press)
            elif index == self.word_len - 1:
                hold_2.append(release - press)
            else:
                hold_1.append(release - press)
                hold_2.append(release - press)
            if index != 0:
                press_press.append(press - self.press[index - 1])

        feature_dict = {}
        for index in range(self.word_len - 1):
            feature_dict[index] = {'hold_1': 0, 'press_press': 0, 'release_press': 0,
                                   'release_release': 0, 'hold_2': 0, 'total_time': 0,
                                   'slope_h1': 0, 'slope_pp': 0, 'slope_rp': 0,
                                   'slope_rr': 0, 'slope_h2': 0, 'slope_tt': 0
                                   }

        for index in range(self.word_len - 1):
            feature_dict[index]['hold_1'] = hold_1[index]
            feature_dict[index]['press_press'] = press_press[index]
            feature_dict[index]['release_press'] = (
                press_press[index] - hold_1[index])
            feature_dict[index]['release_release'] = (
                (press_press[index] - hold_1[index]) + hold_2[index])
            feature_dict[index]['hold_2'] = hold_2[index]
            feature_dict[index]['total_time'] = (
                press_press[index] + hold_2[index])

        for index in range(self.word_len - 1):
            if index != (self.word_len - 2):
                feature_dict[index]['slope_h1'] = self.compute_slope(
                    feature_dict[index + 1]['hold_1'], feature_dict[index]['hold_1'])
                feature_dict[index]['slope_pp'] = self.compute_slope(
                    feature_dict[index + 1]['press_press'], feature_dict[index]['press_press'])
                feature_dict[index]['slope_rp'] = self.compute_slope(
                    feature_dict[index + 1]['release_press'], feature_dict[index]['release_press'])
                feature_dict[index]['slope_rr'] = self.compute_slope(
                    feature_dict[index + 1]['release_release'], feature_dict[index]['release_release'])
                feature_dict[index]['slope_h2'] = self.compute_slope(
                    feature_dict[index + 1]['hold_2'], feature_dict[index]['hold_2'])
                feature_dict[index]['slope_tt'] = self.compute_slope(
                    feature_dict[index + 1]['total_time'], feature_dict[index]['total_time'])

        self.probe_list.append(feature_dict)
        self.reset()

    def compute_slope(self, a, b):
        return a - b

    def start_listener(self):

        timer = time.perf_counter()
        time.sleep(1)
        if self.operation == "identification":
            print('Please, type "il futuro è passato di qui"')
        while self.template_index < self.template_number:

            print('\nStart listener')
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                listener.join()
                current_time = time.perf_counter()
                if current_time - timer > 1:
                    self.reset()
                    timer = current_time

            if self.template_index >= self.template_number:
                break

            time.sleep(0.5)
        print("\nListener stopped")
