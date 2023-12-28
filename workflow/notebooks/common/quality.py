import mixturemapping as mm
import tensorflow as tf
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.stats import wasserstein_distance
from IPython.core.display import display, HTML


def saved_model_test(
        np_inputs,
        tf_inputs,
        pred_gmms
    ):
    """ check if a saved keras model still works
    """

    model_orig = tf.keras.Model(inputs=tf_inputs, outputs=pred_gmms)
    res_orig = model_orig.predict(np_inputs)
    model_orig.save("savedmodel")

    model_loaded = tf.keras.models.load_model("savedmodel")
    res_loaded = model_loaded.predict(np_inputs)

    for k in res_loaded:
        delta = np.max(res_loaded[k]-res_orig[k])
        if delta > 1e-12:
            raise Exception(f"{k} is different in loaded model")

   


def hist_plots(
        np_inputs,
        tf_inputs,
        pred_gmms,
        limit = 10,
        n_samples = 1000):
    """ compare distribution histograms
    """
    
    ideal_gmms = mm.layers.Distribution()({
        "means": tf_inputs["output_means"],
        "covariances": tf_inputs["output_covs"],
        "weights": tf_inputs["output_weights"]
    })
    
    ideal_samples = mm.layers.DistributionSamples(n_samples)(ideal_gmms)
    pred_samples = mm.layers.DistributionSamples(n_samples)(mm.layers.Distribution()(pred_gmms))

    sampleModel = tf.keras.Model(inputs=tf_inputs, outputs=[ideal_samples, pred_samples])

    samplesRes = sampleModel.predict(np_inputs)

    glob_max = np.max(np.max(samplesRes[0], 0), 1)
    glob_min = np.min(np.min(samplesRes[0], 0), 1)

    output_dim = len(glob_max)

    bins = [np.linspace(glob_min[i], glob_max[i], 101) for i in range(output_dim)]

    for i in np.array(range(min(limit, np_inputs["output_means"].shape[0]))):
        display(HTML(f'<h3>Sample {i}</h3>'))
        for k, v in np_inputs.items():
            if "means" in k or "cov" in k:
                print(k, np.mean(v[i], 0))
                continue
            if "weight" in k:
                continue
            print(k, v[i])
        fig = make_subplots(rows=1, cols=output_dim)
        fig.update_layout(width=1200, height=400)
        for dim in range(output_dim):

            counts, binsA = np.histogram(samplesRes[0][i, dim], bins=bins[dim])
            binsC = 0.5 * (binsA[:-1] + binsA[1:])
            figIdeal = px.bar(x=binsC, y=counts)
            figIdeal.data[0].name = f"Ideal {dim}"

            counts, binsA = np.histogram(samplesRes[1][i, dim], bins=bins[dim])
            figPred = px.bar(x=binsC, y=counts)
            figPred.data[0].name = f"Pred {dim}"
            figPred.data[0].opacity=0.5
            figPred.data[0].marker.color = "#fa7c63"

            fig.append_trace(figIdeal.data[0], row=1, col=dim+1)
            fig.append_trace(figPred.data[0], row=1, col=dim+1)

        fig.update_layout(barmode="overlay", bargap=0.0,bargroupgap=0.0)
        fig.show()




def hist_wasserstein_distance(
        np_inputs,
        tf_inputs,
        pred_gmms,
        n_samples = 1000):
    """ compute histograms of the wasserstein distance for all params
    """
    
    ideal_gmms = mm.layers.Distribution()({
        "means": tf_inputs["output_means"],
        "covariances": tf_inputs["output_covs"],
        "weights": tf_inputs["output_weights"]
    })
    
    ideal_samples = mm.layers.DistributionSamples(n_samples)(ideal_gmms)
    pred_samples = mm.layers.DistributionSamples(n_samples)(mm.layers.Distribution()(pred_gmms))

    sampleModel = tf.keras.Model(inputs=tf_inputs, outputs=[ideal_samples, pred_samples])

    samplesRes = sampleModel.predict(np_inputs)



    display(HTML('<h3>Normalized</h3>'))

    distances = np.array(
    [
        [
            wasserstein_distance(samplesRes[1][lot_id][meas_dim], samplesRes[0][lot_id][meas_dim])/np.std(samplesRes[0][lot_id][meas_dim])
            for lot_id in range(samplesRes[0].shape[0])
        ]
        for meas_dim in range(samplesRes[0].shape[1])
    ])

    fig = make_subplots(rows=1, cols=samplesRes[0].shape[1])
    fig.update_layout(width=1200, height=400)
    for meas_dim in range(samplesRes[0].shape[1]):
        fig.append_trace(px.histogram(distances[meas_dim]).data[0], row=1, col=meas_dim+1)
    
    fig.update_layout(barmode="overlay", bargap=0.0,bargroupgap=0.0)
    fig.show()

    print("Distance median:")
    print(np.median(distances, axis=1))

    print("Distance 95%:")
    print(np.quantile(distances, 0.95, axis=1))

    print("Distance 99%:")
    print(np.quantile(distances, 0.99, axis=1))


    display(HTML('<h3>Non Normalized</h3>'))


    

    distances = np.array(
    [
        [
            wasserstein_distance(samplesRes[1][lot_id][meas_dim], samplesRes[0][lot_id][meas_dim])
            for lot_id in range(samplesRes[0].shape[0])
        ]
        for meas_dim in range(samplesRes[0].shape[1])
    ])

    glob_max = np.max(distances, 1)

    fig = make_subplots(rows=1, cols=samplesRes[0].shape[1])
    fig.update_layout(width=1200, height=400)
    for meas_dim in range(samplesRes[0].shape[1]):
        bins = np.linspace(0, glob_max[meas_dim], 51)

        counts, binsA = np.histogram(distances[meas_dim], bins=bins)
        binsC = 0.5 * (binsA[:-1] + binsA[1:])
        subfig = px.bar(x=binsC, y=counts)
        subfig.data[0].name = f"Delta {meas_dim}"

        fig.append_trace(subfig.data[0], row=1, col=meas_dim+1)

    fig.update_layout(barmode="overlay", bargap=0.0,bargroupgap=0.0)
    fig.show()

    print("Distance median:")
    print(np.median(distances, axis=1))

    print("Distance 95%:")
    print(np.quantile(distances, 0.95, axis=1))

    print("Distance 99%:")
    print(np.quantile(distances, 0.99, axis=1))