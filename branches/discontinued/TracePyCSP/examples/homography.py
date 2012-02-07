def Haffine_from_points(fp,tp):
    """ find H, affine transformation, such that 
        tp is affine transf of fp"""

    if fp.shape != tp.shape:
        raise RuntimeError, 'number of points do not match'

    #condition points
    #-from points-
    m = mean(fp[:2], axis=1)
    maxstd = max(std(fp[:2], axis=1))
    C1 = diag([1/maxstd, 1/maxstd, 1]) 
    C1[0][2] = -m[0]/maxstd
    C1[1][2] = -m[1]/maxstd
    fp_cond = dot(C1,fp)

    #-to points-
    m = mean(tp[:2], axis=1)
    C2 = C1.copy() #must use same scaling for both point sets
    C2[0][2] = -m[0]/maxstd
    C2[1][2] = -m[1]/maxstd
    tp_cond = dot(C2,tp)

    #conditioned points have mean zero, so translation is zero
    A = concatenate((fp_cond[:2],tp_cond[:2]), axis=0)
    U,S,V = linalg.svd(A.T)

    #create B and C matrices as Hartley-Zisserman (2:nd ed) p 130.
    tmp = V[:2].T
    B = tmp[:2]
    C = tmp[2:4]

    tmp2 = concatenate((dot(C,linalg.pinv(B)),zeros((2,1))), axis=1) 
    H = vstack((tmp2,[0,0,1]))

    #decondition
    H = dot(linalg.inv(C2),dot(H,C1))

    return H / H[2][2]




def image_in_image(im1,im2,tp):
    """ put im1 in im2 with an affine transformation
        such that corners are as close to tp as possible.
        tp are homogeneous and counter-clockwise from top left.""" 

    #points to warp from
    m,n = im1.shape[:2]
    fp = array([[0,m,m,0],[0,0,n,n],[1,1,1,1]])

    #compute affine transform and apply
    H = Haffine_from_points(tp,fp)
    im1_t = ndimage.affine_transform(im1,H[:2,:2],(H[0,2],H[1,2]),im2.shape[:2])
    alpha = (im1_t > 0)

    return (1-alpha)*im2 + alpha*im1_t


from numpy import *
from PIL import Image
from pylab import *
import warp

#example of affine warp of im1 onto im2
im1 = array(Image.open('beatles.jpg').convert('L'))
im2 = array(Image.open('billboard_for_rent.jpg').convert('L'))

#set from points to corners of im
m,n = im1.shape[:2]
fp = array([[0,m,m,0],[0,0,n,n],[1,1,1,1]])

#set to points
tp = array([[264,538,540,264],[40,36,605,605],[1,1,1,1]])

im3 = warp.image_in_image(im1,im2,tp)

figure()
gray()
imshow(im3)
axis('equal')
axis('off')
show()

