import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config


def save(fig, folder, name, fake):
    if fake:
        fig.suptitle("FAKE DATA")
    fig.tight_layout()
    fig.savefig(folder / name, dpi=150)
    plt.close(fig)


def rig_chart(rigs, rig_mom, folder, fake):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    top.plot(rigs.index, rigs["middle_east"])
    top.set_title("Middle East rig count (Baker Hughes)")
    top.set_ylabel("rigs")
    bottom.plot(rig_mom.index, rig_mom * 100)
    bottom.axhline(0, color="k", linewidth=0.8)
    bottom.set_title(f"{config.MOM_MONTHS}-month change in the rig count")
    bottom.set_ylabel("%")
    for i, b in enumerate(config.RIG_BREAKS):
        label = "definition change" if i == 0 else None
        top.axvline(pd.Timestamp(b), color="gray", linestyle="--", label=label)
        bottom.axvline(pd.Timestamp(b), color="gray", linestyle="--")
    if config.RIG_BREAKS:
        top.legend()
    save(fig, folder, "rig_count.png", fake)


def weights_chart(weights, folder, fake):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for ticker in weights.columns:
        ax.plot(weights.index, weights[ticker] * 100, label=ticker)
    ax.set_title("Middle East share of revenue (exposure weight)")
    ax.set_ylabel("%")
    ax.legend()
    ax.grid(alpha=0.3)
    save(fig, folder, "exposure_weights.png", fake)


def strategy_chart(runs, folder, fake):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, run in runs.items():
        ax.plot((1 + run["net"]).cumprod(), label=name)
    ax.axvline(pd.Timestamp(config.IN_SAMPLE_END), color="gray", linestyle="--",
               label="out of sample starts")
    ax.axhline(1, color="k", linewidth=0.8)
    ax.set_title(f"Growth of 1 after {config.COST_BPS} bps trading costs")
    ax.legend()
    ax.grid(alpha=0.3)
    save(fig, folder, "strategy.png", fake)


def event_chart(paths, folder, fake):
    if paths.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cumulative = paths.cumsum() * 100
    for col in cumulative.columns:
        ax.plot(cumulative.index, cumulative[col], color="lightgray", linewidth=1)
    ax.plot(cumulative.index, cumulative.mean(axis=1), linewidth=2, label="average")
    ax.axhline(0, color="k", linewidth=0.8)
    ax.axvline(0, color="k", linestyle=":")
    ax.set_xlabel("trading days from announcement")
    ax.set_ylabel("cumulative abnormal return (%)")
    ax.set_title(f"Returns around {paths.shape[1]} contract awards")
    ax.legend()
    save(fig, folder, "event_study.png", fake)
