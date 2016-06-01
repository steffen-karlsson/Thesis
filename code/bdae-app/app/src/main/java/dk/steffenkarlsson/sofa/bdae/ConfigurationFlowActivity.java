package dk.steffenkarlsson.sofa.bdae;

import android.animation.Animator;
import android.animation.ArgbEvaluator;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.PorterDuff;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.view.View;
import android.view.animation.DecelerateInterpolator;
import android.view.inputmethod.InputMethodManager;
import android.widget.ImageView;
import android.widget.LinearLayout;

import com.rengwuxian.materialedittext.MaterialEditText;
import com.squareup.otto.Subscribe;

import butterknife.Bind;
import dk.steffenkarlsson.sofa.bdae.event.TransitionAnimationEndedEvent;

/**
 * Created by steffenkarlsson on 6/1/16.
 */
public class ConfigurationFlowActivity extends BaseActivity {

    private static final int TOTAL_DURATION = 500;

    @Bind(R.id.headerContainer)
    protected LinearLayout mHeaderContainer;

    @Bind(R.id.inputContainer)
    protected LinearLayout mInputContainer;

    @Bind(R.id.logo)
    protected ImageView mLogo;

    @Bind(R.id.inputInstanceName)
    protected MaterialEditText mInputInstanceName;

    @Bind(R.id.inputApiHostname)
    protected MaterialEditText mInputApiHostname;

    @Bind(R.id.inputGateway)
    protected MaterialEditText mInputGateway;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    @Subscribe
    public void onTransitionAnimationEnded(TransitionAnimationEndedEvent event) {
        final int finalPosition = (mLogo.getHeight() / 2);
        mInputContainer.setAlpha(0);
        mHeaderContainer.animate()
                .translationYBy(-mHeaderContainer.getTop() - finalPosition)
                .setInterpolator(new DecelerateInterpolator())
                .setDuration(TOTAL_DURATION)
                .setListener(new Animator.AnimatorListener() {
                    @Override
                    public void onAnimationStart(Animator animation) {
                        ValueAnimator anim = ValueAnimator.ofInt(getResources().getColor(R.color.white),
                                getResources().getColor(R.color.colorPrimaryDark));
                        anim.setDuration(TOTAL_DURATION);
                        anim.setEvaluator(new ArgbEvaluator());
                        anim.addListener(new Animator.AnimatorListener() {
                            @Override
                            public void onAnimationStart(Animator animation) { }

                            @Override
                            public void onAnimationEnd(Animator animation) {
                                showKeyboardForView(mInputInstanceName);
                            }

                            @Override
                            public void onAnimationCancel(Animator animation) { }

                            @Override
                            public void onAnimationRepeat(Animator animation) { }
                        });
                        anim.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
                            @Override
                            public void onAnimationUpdate(ValueAnimator animation) {
                                mLogo.setColorFilter((Integer) animation.getAnimatedValue(), PorterDuff.Mode.SRC_ATOP);
                            }
                        });
                        anim.start();
                    }

                    @Override
                    public void onAnimationEnd(Animator animation) {
                        mHeaderContainer.setTranslationY(-finalPosition);
                        mInputContainer.setVisibility(View.VISIBLE);
                        mInputContainer.animate()
                                .alpha(100f)
                                .setDuration(TOTAL_DURATION)
                                .start();
                    }

                    @Override
                    public void onAnimationCancel(Animator animation) {

                    }

                    @Override
                    public void onAnimationRepeat(Animator animation) {

                    }
                }).start();
    }

    private void showKeyboardForView(View view) {
        view.requestFocus();
        InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
        imm.showSoftInput(view, InputMethodManager.SHOW_IMPLICIT);
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.activity_configuration_flow;
    }

    @Override
    protected int getTitleResource() {
        return -1;
    }

    @Override
    protected boolean hasLoadingSpinner() {
        return false;
    }

    @Override
    protected boolean showActionBar() {
        return false;
    }
}
