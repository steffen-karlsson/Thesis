package dk.steffenkarlsson.sofa.bdae;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;

import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public interface IActivityHandler {
    Context getContext();
    Activity getActivity();
    void setLoadingSpinnerVisible(boolean visible);
    void setNoDataVisible(boolean visible);
    Intent getActivityIntent(Context context, Class clzz, boolean killOnBackPressed);
    Intent getActivityIntent(Context context, Class clzz);
    void launchActivity(Intent intent, TransitionAnimation transitionAnimation);
    void refreshOptionsMenu();
}
