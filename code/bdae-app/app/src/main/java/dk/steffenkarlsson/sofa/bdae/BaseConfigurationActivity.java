package dk.steffenkarlsson.sofa.bdae;

import android.os.Handler;

import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;
import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;

/**
 * Created by steffenkarlsson on 6/1/16.
 */
public abstract class BaseConfigurationActivity extends BaseActivity {

    private final Handler mHandler = new Handler();
    private boolean mIsOverlayVisible = false;

    @Override
    protected void onResume() {
        super.onResume();

        if (requiresConfiguration() && !getConfiguration().hasData()) {
            startConfigureFlow();
        }
    }

    private void startConfigureFlow() {
        mHandler.removeCallbacks(mDelayedConfigurationOverlay);
        mHandler.postDelayed(mDelayedConfigurationOverlay, 600);
    }

    private Runnable mDelayedConfigurationOverlay = new Runnable() {
        @Override
        public void run() {
            if (!mIsOverlayVisible) {
                mIsOverlayVisible = true;
                BaseConfigurationActivity.super.launchActivity(getActivityIntent(
                        getApplicationContext(), ConfigurationFlowActivity.class, true),
                        TransitionAnimation.IN_FROM_BOTTOM);
            }
        }
    };

    protected abstract boolean requiresConfiguration();

    @Override
    protected boolean hasLoadingSpinner() {
        return false;
    }

    protected ConfigurationHandler getConfiguration() {
        return ConfigurationHandler.getInstance();
    }
}
