import pandas as pd
import os
import subprocess


class FioManager:
    def __init__(
        self,
        name,
        bs="4M",
        rw="randread",
        size="100M",
        numjobs=4,
        iodepth=32,
        direct=1,
        ioengine="libaio",
        runtime=10,
        extra_opts=None,
    ):
        self.name = name
        self.bs = bs
        self.rw = rw
        self.size = size
        self.numjobs = numjobs
        self.iodepth = iodepth
        self.direct = direct
        self.ioengine = ioengine
        self.runtime = runtime
        self.extra_opts = extra_opts or {}

    def build_cmd(self, filename, output_format="json"):
        cmd = [
            "fio",
            f"--name={self.name}",
            f"--rw={self.rw}",
            f"--size={self.size}",
            f"--bs={self.bs}",
            f"--direct={self.direct}",
            f"--filename={filename}",
            f"--numjobs={self.numjobs}",
            f"--ioengine={self.ioengine}",
            f"--iodepth={self.iodepth}",
            f"--runtime={self.runtime}",
            "--group_reporting",
            "--time_based"
        ]
        if output_format:
            cmd.append(f"--output-format={output_format}")
        for k, v in self.extra_opts.items():
            cmd.append(f"--{k}={v}")
        return cmd

    def run(self, filename, output_format="json"):
        import json
        cmd = self.build_cmd(filename, output_format=output_format)
        # print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if output_format == "json":
            try:
                fio_json = json.loads(result.stdout)
            except Exception as e:
                fio_json = {"error": str(e), "stdout": result.stdout, "stderr": result.stderr}
            return fio_json
        return result.stdout, result.stderr


class FioFileTest(FioManager):
    def run_test(self, path, output_format="json"):
        return self.run(path, output_format=output_format)


class FioDirTest(FioManager):
    def run_test(self, path, output_format="json"):
        temp_file = os.path.join(path, f"{self.name}_fio_temp.dat")
        result = self.run(temp_file, output_format=output_format)
        try:
            os.remove(temp_file)
        except Exception:
            pass
        return result


# FioResult is now a DataFrame subclass
class FioResult(pd.DataFrame):
    """
    DataFrame subclass for fio results. Construct with FioResult.from_fio_json(fio_json).
    """
    _metadata = ["raw"]

    def __init__(self, *args, raw=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw = raw

    @classmethod
    def from_fio_json(cls, fio_json):
        """
        Only include fields useful for basic drive benchmarking:
        - jobname
        - <op>_iops
        - <op>_bw (bandwidth in KB/s)
        - <op>_lat_mean (average latency in usec)
        """
        if not isinstance(fio_json, dict) or "jobs" not in fio_json:
            raise ValueError("Invalid fio JSON structure")
        jobs = fio_json["jobs"]
        records = []
        for job in jobs:
            rec = {"jobname": job.get("jobname")}
            for op in ("read", "write", "trim"):
                if op in job:
                    if "iops" in job[op]:
                        rec[f"{op}_iops"] = job[op]["iops"]
                    if "bw" in job[op]:
                        rec[f"{op}_bw"] = job[op]["bw"]
                    # Latency can be in 'lat' or 'clat' depending on fio version/config
                    lat = job[op].get("lat") or job[op].get("clat")
                    if lat and "mean" in lat:
                        rec[f"{op}_lat_mean"] = lat["mean"]
            records.append(rec)
        df = cls(records, raw=fio_json)
        return df
