from __future__ import division
import numpy as np

from keras.callbacks import EarlyStopping, TensorBoard
from keras.layers import Input, Dropout
from keras.models import Model
from keras.optimizers import Adam
from keras.regularizers import l2

from keras_gat import GraphAttention
from keras_gat.utils import load_data

# Read data
A, X, Y_train, Y_val, Y_test, idx_train, idx_val, idx_test = load_data('cora')

# Parameters
N = X.shape[0]                # Number of nodes in the graph
F = X.shape[1]                # Original feature dimesnionality
n_classes = Y_train.shape[1]  # Number of classes
F_ = 8                        # Output dimension of first GraphAttention layer
n_attn_heads = 8              # Number of attention heads in first GAT layer
dropout_rate = 0.6            # Dropout rate applied to the input of GAT layers
l2_reg = 5e-4                 # Regularization rate for l2
learning_rate = 5e-3          # Learning rate for SGD
epochs = 2000                 # Number of epochs to run for
es_patience = 100             # Patience fot early stopping

# Preprocessing operations
X /= X.sum(1).reshape(-1, 1)
A = A + np.eye(A.shape[0])  # Add self-loops

# Model definition (as per Section 3.3 of the paper)
X_in = Input(shape=(F,))
A_in = Input(shape=(N,))

dropout1 = Dropout(dropout_rate)(X_in)
graph_attention_1 = GraphAttention(F_,
                                   attn_heads=n_attn_heads,
                                   attn_heads_reduction='concat',
                                   activation='elu',
                                   kernel_regularizer=l2(l2_reg))([dropout1, A_in])
dropout2 = Dropout(dropout_rate)(graph_attention_1)
graph_attention_2 = GraphAttention(n_classes,
                                   attn_heads=1,
                                   attn_heads_reduction='average',
                                   activation='softmax',
                                   kernel_regularizer=l2(l2_reg))([dropout2, A_in])

# Build model
model = Model(inputs=[X_in, A_in], outputs=graph_attention_2)
optimizer = Adam(lr=learning_rate)
model.compile(optimizer=optimizer,
              loss='categorical_crossentropy',
              weighted_metrics=['acc'])
model.summary()

# Callbacks
es_callback = EarlyStopping(monitor='val_weighted_acc', patience=es_patience)
tb_callback = TensorBoard(batch_size=N)

# Train model
validation_data = ([X, A], Y_val, idx_val)
model.fit([X, A],
          Y_train,
          sample_weight=idx_train,
          epochs=epochs,
          batch_size=N,
          validation_data=validation_data,
          shuffle=False,  # Shuffling data means shuffling the whole graph
          callbacks=[es_callback, tb_callback])

# Evaluate model
eval_results = model.evaluate([X, A],
                              Y_test,
                              sample_weight=idx_test,
                              batch_size=N,
                              verbose=0)
print('Done.\n'
      'Test loss: {}\n'
      'Test accuracy: {}'.format(*eval_results))
