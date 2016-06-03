package dk.steffenkarlsson.sofa.bdae;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;

import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public interface IActivityHandler {
    Context getContext();
    Activity getActivity();
    void setActionbarTitle(String title);
    void setActionbarTitle(int titleResId);
    void setLoadingSpinnerVisible(boolean visible);
    void setNoDataVisible(boolean visible);
    Intent getActivityIntent(Context context, Class clzz, boolean killOnBackPressed);
    Intent getActivityIntent(Context context, Class clzz);
    Intent getActivityIntent(Context context, Class clzz, Bundle extras, boolean killOnBackPressed);
    void launchActivity(Intent intent, TransitionAnimation transitionAnimation);
    void refreshOptionsMenu();
}
