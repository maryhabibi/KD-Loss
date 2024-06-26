from configuration import DatasetName, DatasetType, \
    D300wConf, InputDataSize, LearningConfig

import tensorflow as tf
# tf.compat.v1.disable_eager_execution()

from tensorflow import keras
from skimage.transform import resize
from keras.regularizers import l2

# tf.logging.set_verbosity(tf.logging.ERROR)
from tensorflow.keras.models import Model
from tensorflow.keras.applications import mobilenet_v2, mobilenet, resnet50, densenet

from tensorflow.keras.layers import Dense, MaxPooling2D, Conv2D, Flatten, \
    BatchNormalization, Activation, GlobalAveragePooling2D, DepthwiseConv2D, Dropout, ReLU, Concatenate, Input, Conv2DTranspose

from keras.callbacks import ModelCheckpoint
from keras import backend as K

from keras.optimizers import Adam
import numpy as np
import matplotlib.pyplot as plt
import math
from keras.callbacks import CSVLogger
from datetime import datetime

import cv2
import os.path
from keras.utils.vis_utils import plot_model
from scipy.spatial import distance
import scipy.io as sio

import efficientnet.tfkeras as efn


class CNNModel:
    def get_model(self, arch, input_tensor, output_len,
                  inp_shape=[InputDataSize.image_input_size, InputDataSize.image_input_size, 3],
                  weight_path=None):
        if arch == 'efficientNet':
            model = self.create_efficientNet(inp_shape=inp_shape, input_tensor=input_tensor, output_len=output_len)
        elif arch == 'mobileNetV2':
            model = self.create_MobileNet(inp_shape=inp_shape, inp_tensor=input_tensor)
        return model

    def create_MobileNet(self, inp_shape, inp_tensor):

        mobilenet_model = mobilenet_v2.MobileNetV2(input_shape=inp_shape,
                                                   alpha=1.0,
                                                   include_top=True,
                                                   weights=None,
                                                   input_tensor=inp_tensor,
                                                   pooling=None)

        inp = mobilenet_model.input
        out_landmarks = mobilenet_model.get_layer('O_L').output
        revised_model = Model(inp, [out_landmarks])
        model_json = revised_model.to_json()
        with open("mobileNet_v2_stu.json", "w") as json_file:
            json_file.write(model_json)
        return revised_model

    def create_efficientNet(self, inp_shape, input_tensor, output_len, is_teacher=True):
        if is_teacher:  # for teacher we use a heavier network
            eff_net = efn.EfficientNetB3(include_top=True,
                                         weights=None,
                                         input_tensor=None,
                                         input_shape=[InputDataSize.image_input_size, InputDataSize.image_input_size,
                                                      3],
                                         pooling=None,
                                         classes=output_len)
        else:  # for student we use the small network
            eff_net = efn.EfficientNetB0(include_top=True,
                                         weights=None,
                                         input_tensor=None,
                                         input_shape=inp_shape,
                                         pooling=None,
                                         classes=output_len)  # or weights='noisy-student'

        eff_net.layers.pop()
        inp = eff_net.input

        x = eff_net.get_layer('top_activation').output
        x = GlobalAveragePooling2D()(x)
        x = keras.layers.Dropout(rate=0.5)(x)
        output = Dense(output_len, activation='linear', name='out')(x)

        eff_net = Model(inp, output)

        eff_net.summary()

        return eff_net

