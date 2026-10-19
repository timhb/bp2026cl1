# Using Slurm on the cluster

Always pass our project account: `-A sci-lippert-bp2026cl1`.

## Partitions

| Partition | Use | Time limit |
| --- | --- | --- |
| `pot-hpi-cpu-interactive` (default) | CPU shell, setup, checks | 8 h |
| `pot-hpi-cpu-batch` | CPU batch jobs | 7 days |
| `pot-hpi-gpu-interactive` | GPU shell, debugging | 8 h |
| `pot-hpi-gpu-shortrun` | Quick GPU tests | 1 h |
| `pot-hpi-gpu-batch` | GPU training | 7 days |

GPU types (`--gres=gpu:TYPE:N`): `a100`, `h100`, `b200`, `a40`, `l40`, `a30`, `rtx_pro_6000`.
Not every partition has every type; check with `sinfo` below.

## Check available resources

```bash
sinfo -s                                   # partitions and node states (A/I/O/T = allocated/idle/other/total)
sinfo -p pot-hpi-gpu-batch -o "%n %G %c %m %t"   # per-node GPUs, CPUs, memory (MB), state
squeue -p pot-hpi-gpu-batch                # who is queued/running
```

## Reserve an interactive node

```bash
srun -A sci-lippert-bp2026cl1 -p pot-hpi-gpu-interactive \
     --gres=gpu:a100:1 --cpus-per-task=8 --mem=64G --time=02:00:00 \
     --pty bash
```

| Flag | Meaning |
| --- | --- |
| `--time=HH:MM:SS` | Runtime; job is killed afterwards. Shorter jobs start sooner. |
| `--gres=gpu:a100:2` | GPU type and count. |
| `--cpus-per-task=8` | CPU cores. |
| `--mem=64G` | RAM per node. Default is only 1.5 GB per CPU. |

Exit the shell to release the node.

## Submit a batch job

`scripts/train.sbatch`:

```bash
#!/bin/bash
#SBATCH -A sci-lippert-bp2026cl1
#SBATCH -p pot-hpi-gpu-batch
#SBATCH --job-name=train
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%j.out   # %x = job name, %j = job id

pixi run python -m bp26.train
```

```bash
mkdir -p logs
sbatch scripts/train.sbatch
```

## Monitor jobs

```bash
squeue --me                       # your jobs (PD = pending, R = running)
tail -f logs/train-<jobid>.out    # live output
scontrol show job <jobid>         # details, incl. why it is pending
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS   # after it finished
scancel <jobid>                   # cancel
```

On a running GPU node: `srun --jobid=<jobid> --overlap nvidia-smi`.
