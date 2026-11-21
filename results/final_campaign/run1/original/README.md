# RUN1 original evidence (copied from the measurement machine)

Files exactly as produced/used on the machine (i7-13650HX, governor performance, AC power):

- raw.csv          760 runs = 8 images x (5 sequential + 90 MPI); columns: image,mode,strategy,np,rep,LBG_s,Total_s,ok,md5
- env.txt          machine, compiler, MPI, governor, NPS/REPS/binding, md5 of the two programs and of the 8 input images
- memory_RUN1.csv  peak RSS per process (P = 1, 4, 14; 3 repetitions)
- codes_min.c      sequential program used for RUN1 (md5 95b00142...)
- codep_min.c      parallel program used for RUN1   (md5 cc149a27...)
- run_all_once.sh  script that produced raw.csv and env.txt

Checks done on raw.csv: 760 rows, ok = 1 in every row, one distinct md5 of the compressed container per image
across all 95 runs of that image. The times match results/final_campaign/run1/raw_RUN1.csv row by row.
