package dk.steffenkarlsson.sofa.bdae.extra;

import dk.steffenkarlsson.sofa.bdae.R;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public enum TransitionAnimation {
    DEFAULT, IN_FROM_RIGHT, IN_FROM_BOTTOM, OUT_RIGHT, OUT_BOTTOM, FADE_IN, FADE_OUT;

    public static int getAnimation(TransitionAnimation transitionAnimation) {
        switch (transitionAnimation) {
            case IN_FROM_BOTTOM:
                return R.anim.in_from_bottom;
            case OUT_RIGHT:
                return R.anim.out_right;
            case OUT_BOTTOM:
                return R.anim.out_bottom;
            case FADE_IN:
                return R.anim.fade_in;
            case FADE_OUT:
                return R.anim.fade_out;
            case IN_FROM_RIGHT:
            case DEFAULT:
            default:
                return R.anim.in_from_right;
        }
    }

    public static int getOutAnimation(TransitionAnimation transitionAnimation) {
        switch (transitionAnimation) {
            case IN_FROM_BOTTOM:
                return R.anim.out_bottom;
            case FADE_IN:
                return R.anim.fade_out;
            case IN_FROM_RIGHT:
            case DEFAULT:
            default:
                return R.anim.out_right;
        }
    }

}