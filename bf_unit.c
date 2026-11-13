/* bf_unit.c: proves the row-band filter equals the full-image filter for many row splits.
 * Build: mpicc -O2 -o bf_unit bf_unit.c -lm      Run: ./bf_unit gray.txt   (pam2_bf.c in same folder) */
#define main pam_main
#include "pam2_bf.c"
#undef main
#include <assert.h>
int main(int argc,char**argv){
  uint8_t *img=malloc(WIDTH*HEIGHT),*full=malloc(WIDTH*HEIGHT),*asm_=malloc(WIDTH*HEIGHT);
  if(!read_image_from_txt(argv[1],img,WIDTH,HEIGHT)) return 1;
  bilateral_preprocess(img,full,WIDTH,HEIGHT,BF_D,BF_SIGMA_COLOR,BF_SIGMA_SPACE,BF_ALPHA);
  srand(11); int tests=0, bad=0;
  int sizes[]={1,2,3,4,6,8,10,12,14,16,20,37};
  for(unsigned si=0;si<sizeof sizes/sizeof *sizes;si++){
    int size=sizes[si];
    for(int mode=0;mode<3;mode++){           /* 0: equal, 1: random speeds, 2: extreme (some ranks tiny) */
      int nv=(WIDTH/BLOCK_SIZE)*(HEIGHT/BLOCK_SIZE); int *vc=malloc(size*sizeof(int)); long tot=0; double *w=malloc(size*sizeof(double)); double sw=0;
      for(int r=0;r<size;r++){ w[r]= mode==0?1.0: mode==1? 0.3+ (rand()%100)/40.0 : (r%3==0?0.01:3.0); sw+=w[r]; }
      int assigned=0; for(int r=0;r<size;r++){ vc[r]=(int)(nv*w[r]/sw); assigned+=vc[r]; } vc[size-1]+=nv-assigned; (void)tot;
      int *ys=malloc((size+1)*sizeof(int)); bf_row_bounds(size,vc,nv,ys);
      int ok = ys[0]==0 && ys[size]==HEIGHT; for(int r=0;r<size;r++) ok = ok && ys[r+1]>=ys[r];
      memset(asm_,0,WIDTH*HEIGHT);
      for(int r=0;r<size;r++){ int rows=ys[r+1]-ys[r]; if(rows<=0) continue;
        uint8_t *band=malloc((size_t)rows*WIDTH);
        bilateral_rows(img,band,WIDTH,HEIGHT,ys[r],ys[r+1],BF_D,BF_SIGMA_COLOR,BF_SIGMA_SPACE,BF_ALPHA);
        memcpy(asm_+(size_t)ys[r]*WIDTH,band,(size_t)rows*WIDTH); free(band); }
      ok = ok && memcmp(asm_,full,WIDTH*HEIGHT)==0;
      tests++; if(!ok){bad++; printf("FAIL size=%d mode=%d\n",size,mode);} free(vc);free(w);free(ys);
    }
  }
  printf("row-band assembly vs full-image filter: %d/%d configurations bit-identical\n",tests-bad,tests);
  return bad!=0;
}
