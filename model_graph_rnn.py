# -*- coding: utf-8 -*-
"""
Created on Sat Aug 25 15:33:42 2018

@author: limingfan

"""

import tensorflow as tf

from zoo_layers import rnn_layer
from zoo_layers import att_pool_layer

debug_tensor_name = "to_be_assigned"


def build_model_graph(settings, data):
    
    input_x, input_y = data

    with tf.device('/cpu:0'):
        
        input_x = tf.identity(input_x, name = "input_x")
        input_y = tf.identity(input_y, name = "input_y")
        
        #
        emb_mat = tf.get_variable('embedding',
                                  [settings.vocab.size(), settings.vocab.emb_dim],
                                  initializer=tf.constant_initializer(settings.vocab.embeddings),
                                  trainable = settings.emb_tune)
        seq_emb = tf.nn.embedding_lookup(emb_mat, input_x)
        
        seq_mask = tf.cast(tf.cast(input_x, dtype = tf.bool), dtype = tf.int32)
        seq_len = tf.reduce_sum(seq_mask, 1)

    with tf.name_scope("rnn"):
        
        seq_e = rnn_layer(seq_emb, seq_len, 128, settings.keep_prob,
                          activation = tf.nn.relu, concat = True, scope = 'bi-lstm-1')        
               
        B = tf.shape(seq_e)[0]
        query = tf.get_variable("query", [settings.att_dim],
                                initializer = tf.ones_initializer())
        query = tf.tile(tf.expand_dims(query, 0), [B, 1])

        feat = att_pool_layer(seq_e, query, seq_mask, settings.att_dim,
                              settings.keep_prob, is_train=None, scope="att_pooling")
        
        #feat = seq_e[:,-1,:]

    with tf.name_scope("score"):
        #
        fc = tf.nn.dropout(feat, settings.keep_prob)
        fc = tf.layers.dense(fc, 128, name='fc1')            
        fc = tf.nn.relu(fc)
        
        fc = tf.nn.dropout(fc, settings.keep_prob)
        logits = tf.layers.dense(fc, settings.num_classes, name='fc2')
        # logits = tf.nn.sigmoid(fc)
        
        normed_logits = tf.nn.softmax(logits, name='logits')
        
    with tf.name_scope("loss_infer"):
        #
        cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits = logits,
                                                                       labels = input_y)
        loss_infer = tf.reduce_mean(cross_entropy, name = 'loss_infer')

    with tf.name_scope("accuracy"):
        #
        y_pred_cls = tf.argmax(logits, 1, name='pred_cls')
        correct_pred = tf.equal(input_y, y_pred_cls)
        acc = tf.reduce_mean(tf.cast(correct_pred, tf.float32), name = 'metric')
    
    #
    if settings.keep_prob < 1.0:  # train, eval
        print(input_x)
        print(input_y)
        #
        print(normed_logits)
        print(acc)
        print(loss_infer)
        print()
    #

    #
    debug_tensor = normed_logits
    #
    
    #
    global debug_tensor_name
    debug_tensor_name = debug_tensor.name
    #
    if settings.keep_prob < 1.0:
        print('debug_tensor_name: ' + debug_tensor_name)
        print(debug_tensor)
        print()
    #
    
    #
    return normed_logits, acc, loss_infer
    # results, metric, loss
    #
    
def debug_the_model(model, data_batches):
    
    model.log_info("begin debug ...")    
    model_graph, model_sess = model.get_model_graph_and_sess()
    
    idx_batch = 0
    
    data_batch = data_batches[idx_batch]
    
    print()
    for item in zip(*data_batch):
        #
        print(item[-1])
        print(model.vocab.convert_ids_to_tokens(item[0]) )
    print()
    
    #
    global debug_tensor_name
    tensor = model_graph.get_tensor_by_name(debug_tensor_name)
    #
    tensor_v = model_sess.run(tensor, feed_dict = model.feed_data_train(data_batch))    
    print(tensor_v)
    print(tensor_v.shape)
    
    loss = model_graph.get_tensor_by_name('loss/loss:0')
    loss_v = model_sess.run(loss, feed_dict = model.feed_data_train(data_batch))    
    print(loss_v)
    
    return tensor_v
    #
    
