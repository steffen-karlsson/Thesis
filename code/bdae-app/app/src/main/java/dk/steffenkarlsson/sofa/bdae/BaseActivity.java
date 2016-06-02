package dk.steffenkarlsson.sofa.bdae;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.support.annotation.LayoutRes;
import android.support.annotation.Nullable;
import android.support.annotation.StringRes;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.View;
import android.widget.ProgressBar;

import butterknife.BindView;
import butterknife.ButterKnife;
import dk.steffenkarlsson.sofa.bdae.event.TransitionAnimationEndedEvent;
import dk.steffenkarlsson.sofa.bdae.extra.EventBus;
import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public abstract class BaseActivity extends AppCompatActivity {

    private static final String BUNDLE_TRANSITION = "BUNDLE_TRANSITION";

    @Nullable @BindView(R.id.toolbar)
    protected Toolbar mToolbar;

    @Nullable @BindView(R.id.progress)
    protected ProgressBar mLoadingSpinner;

    private TransitionAnimation mOutTransition;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int layoutRes = getLayoutResource();
        if (layoutRes == -1)
            throw new RuntimeException("No layout defined in getLayoutResource");

        setContentView(layoutRes);
        ButterKnife.setDebug(true);
        ButterKnife.bind(this);
        EventBus.getInstance().register(this);

        mOutTransition = TransitionAnimation.values()[getIntent().getIntExtra(BUNDLE_TRANSITION, 0)];
        getIntent().removeExtra(BUNDLE_TRANSITION);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        EventBus.getInstance().unregister(this);
    }

    @Override
    protected void onResume() {
        super.onResume();

        if (hasLoadingSpinner() && mLoadingSpinner != null)
            mLoadingSpinner.getIndeterminateDrawable().setColorFilter(
                    getResources().getColor(R.color.colorSpinner),
                    android.graphics.PorterDuff.Mode.MULTIPLY);

        initActionBar();
    }

    protected void initActionBar() {
        if (showActionBar()) {
            setSupportActionBar(mToolbar);

            if (getTitleResource() != -1)
                setActionbarTitle(getTitleResource());

            if (getSupportActionBar() != null) {
                getSupportActionBar().setDisplayShowHomeEnabled(true);
                getSupportActionBar().setHomeButtonEnabled(true);

                if (showBackButton()) {
                    getSupportActionBar().setDisplayHomeAsUpEnabled(true);
                }
            }
        }
    }

    @LayoutRes
    protected abstract int getLayoutResource();

    @StringRes
    protected abstract int getTitleResource();

    protected boolean hasLoadingSpinner() {
        return true;
    }

    protected boolean showBackButton() {
        return false;
    }

    protected boolean showActionBar() {
        return true;
    }

    protected void setActionbarTitle(int titleResId) {
        setActionbarTitle(getString(titleResId));
    }

    protected void setActionbarTitle(String title) {
        if (getSupportActionBar() != null && showActionBar()) {
            getSupportActionBar().setTitle(title);
        }
    }

    protected void setLoadingSpinnerVisible(boolean visible) {
        if (hasLoadingSpinner())
            mLoadingSpinner.setVisibility(visible ? View.VISIBLE : View.INVISIBLE);
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        applyBackTransition();
    }

    protected void applyBackTransition() {
        overridePendingTransition(
                TransitionAnimation.getAnimation(TransitionAnimation.FADE_IN),
                TransitionAnimation.getOutAnimation(mOutTransition)
        );
    }

    protected void applyInTransition(TransitionAnimation inAnimation) {
        overridePendingTransition(
                TransitionAnimation.getAnimation(inAnimation),
                TransitionAnimation.getAnimation(TransitionAnimation.FADE_OUT)
        );
        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                EventBus.getInstance().post(new TransitionAnimationEndedEvent());
            }
        }, 700);
    }

    public void launchActivity(Intent intent, TransitionAnimation transitionAnimation) {
        intent.putExtra(BUNDLE_TRANSITION, transitionAnimation.ordinal());
        startActivity(intent);
        applyInTransition(transitionAnimation);
    }

    public void launchActivityForResult(Intent intent, int requestCode, TransitionAnimation transitionAnimation) {
        intent.putExtra(BUNDLE_TRANSITION, transitionAnimation.ordinal());
        startActivityForResult(intent, requestCode);
        applyInTransition(transitionAnimation);
    }

    public Intent getActivityIntent(Context context, Class clzz, boolean killOnBackPressed) {
        return getActivityIntent(context, clzz, null, killOnBackPressed);
    }

    public Intent getActivityIntent(Context context, Class clzz) {
        return getActivityIntent(context, clzz, null, false);
    }

    public Intent getActivityIntent(Context context, Class clzz, Bundle extras, boolean killOnBackPressed) {
        Intent intent = new Intent(context, clzz);
        if (extras != null)
            intent.putExtras(extras);

        if (killOnBackPressed)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        else
            intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);

        return intent;
    }
}
