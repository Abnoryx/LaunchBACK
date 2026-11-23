# SSIM (quarter-res luma) between our frames and reference video frames.
import sys, subprocess, glob, os, numpy as np
from PIL import Image
def luma(img): a=np.asarray(img.convert('L').resize((270,480),Image.BILINEAR)).astype(np.float64); return a
def ssim(x,y):
    from numpy.lib.stride_tricks import sliding_window_view as sw
    C1,C2=(0.01*255)**2,(0.03*255)**2
    k=7; X=sw(x,(k,k)); Y=sw(y,(k,k))
    mx,my=X.mean((-1,-2)),Y.mean((-1,-2)); vx,vy=X.var((-1,-2)),Y.var((-1,-2)); cxy=((X-mx[...,None,None])*(Y-my[...,None,None])).mean((-1,-2))
    return float((((2*mx*my+C1)*(2*cxy+C2))/((mx**2+my**2+C1)*(vx+vy+C2))).mean())
frames_dir, ref, fps = sys.argv[1], sys.argv[2], float(sys.argv[3])
out=[]
for f in sorted(glob.glob(frames_dir+'/f*.png')):
    n=int(os.path.basename(f)[1:-4]); t=n/fps
    raw=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',ref,'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True).stdout
    import io; r=Image.open(io.BytesIO(raw))
    s=ssim(luma(Image.open(f)),luma(r)); out.append(s); print(f"t={t:6.2f} ssim={s:.3f}")
print(f"mean ssim {np.mean(out):.3f}  min {np.min(out):.3f}")
