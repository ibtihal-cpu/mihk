/* Mechanism test: does the ORDER/PRECISION of the per-cluster accumulation change the number of LBG iterations?
   Emulates what np ranks do: each chunk accumulates its own partial sums (float), then partials are added.
   nchunks=1 is the sequential code. acc_double=1 accumulates sums/distortion in double. */
#define main sem1_main
#include "sem_v2.c"
#undef main

static int lbg_variant(const float *training, int nv, int K, uint8_t *labels, float *codebook, int nchunks, int acc_double)
{
    for (int j = 0; j < VLEN; j++) { float s = 0; for (int i = 0; i < nv; i++) s += training[i*VLEN+j]; codebook[j] = s / nv; }
    int k = 1, total = 0;
    while (k < K) {
        for (int i = 0; i < k; i++) for (int j = 0; j < VLEN; j++) {
            codebook[(k+i)*VLEN+j] = codebook[i*VLEN+j]*(1.0f-DELTA); codebook[i*VLEN+j] = codebook[i*VLEN+j]*(1.0f+DELTA); }
        k *= 2;
        float prev = 1e30f; int it = 0; float improvement = 1.0f;
        do {
            double *sd = calloc((size_t)k*VLEN, sizeof(double)); float *sf = calloc((size_t)k*VLEN, sizeof(float));
            double *cd = calloc(k, sizeof(double)); double dist_d = 0; float dist_f = 0;
            for (int ch = 0; ch < nchunks; ch++) {
                int a = (int)((long)nv*ch/nchunks), b = (int)((long)nv*(ch+1)/nchunks);
                float *pf = calloc((size_t)k*VLEN, sizeof(float)); double *pd = calloc((size_t)k*VLEN, sizeof(double));
                float pdist_f = 0; double pdist_d = 0;
                for (int i = a; i < b; i++) {
                    float md = 1e30f; int mi = 0; const float *v = &training[i*VLEN];
                    for (int c = 0; c < k; c++) { float dd = distance16(&codebook[c*VLEN], v); if (dd < md) { md = dd; mi = c; } }
                    labels[i] = (uint8_t)mi; cd[mi] += 1.0; pdist_f += md; pdist_d += md;
                    for (int j = 0; j < VLEN; j++) { if (acc_double) pd[mi*VLEN+j] += v[j]; else pf[mi*VLEN+j] += v[j]; }
                }
                for (int x = 0; x < k*VLEN; x++) { if (acc_double) sd[x] += pd[x]; else sf[x] += pf[x]; }
                dist_f += pdist_f; dist_d += pdist_d; free(pf); free(pd);
            }
            for (int c = 0; c < k; c++) if (cd[c] > 0) for (int j = 0; j < VLEN; j++)
                codebook[c*VLEN+j] = acc_double ? (float)(sd[c*VLEN+j]/cd[c]) : sf[c*VLEN+j]*(1.0f/(float)cd[c]);
            float dnow = acc_double ? (float)(dist_d/nv) : dist_f/nv;
            improvement = fabsf(prev - dnow) / (dnow + 1e-9f); prev = dnow; it++;
            free(sd); free(sf); free(cd);
        } while (it < 100 && improvement > EPSILON);
        total += it;
    }
    return total;
}

int main(int argc, char **argv)
{
    int npl[] = {1, 2, 4, 8};
    printf("%-14s | float sums, chunks=1/2/4/8      | double sums, chunks=1/2/4/8\n", "plane");
    for (int a = 1; a < argc; a++) {
        ImgMode m = detect_mode_from_file(argv[a]); if (m == MODE_UNKNOWN) continue;
        uint8_t *pl[3]; for (int p = 0; p < 3; p++) pl[p] = malloc(WIDTH*HEIGHT);
        if (m == MODE_COLOR) read_color_image_from_txt(argv[a], pl[0], pl[1], pl[2], WIDTH, HEIGHT); else read_image_from_txt(argv[a], pl[0], WIDTH, HEIGHT);
        for (int p = 0; p < (m == MODE_COLOR ? 3 : 1); p++) {
            uint8_t *tr = NULL; int nv = build_training_vectors(pl[p], &tr);
            float *tf = calloc((size_t)nv*VLEN, sizeof(float)); uint8_t *lab = malloc(nv);
            for (int i = 0; i < nv*VLEN; i++) tf[i] = (float)tr[i];
            int r[2][4];
            for (int d = 0; d < 2; d++) for (int q = 0; q < 4; q++) { float cb[CODEBOOK_SIZE*VLEN] = {0}; r[d][q] = lbg_variant(tf, nv, CODEBOOK_SIZE, lab, cb, npl[q], d); }
            const char *nm = strrchr(argv[a], '/'); nm = nm ? nm+1 : argv[a];
            printf("%-10s p%d  | %4d %4d %4d %4d              | %4d %4d %4d %4d\n", nm, p, r[0][0], r[0][1], r[0][2], r[0][3], r[1][0], r[1][1], r[1][2], r[1][3]);
            free(tr); free(tf); free(lab);
        }
    }
    return 0;
}
