package dk.steffenkarlsson.sofa.bdae;

import android.animation.Animator;
import android.animation.ArgbEvaluator;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.PorterDuff;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.util.Patterns;
import android.view.View;
import android.view.animation.DecelerateInterpolator;
import android.view.inputmethod.InputMethodManager;
import android.widget.ImageView;
import android.widget.LinearLayout;

import com.rengwuxian.materialedittext.MaterialEditText;
import com.squareup.otto.Subscribe;

import java.util.ArrayList;

import butterknife.BindView;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.event.TransitionAnimationEndedEvent;
import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;
import dk.steffenkarlsson.sofa.bdae.extra.ChangedTextWatcher;

/**
 * Created by steffenkarlsson on 6/1/16.
 */
public class ConfigurationFlowActivity extends BaseActivity {

    private static final int TOTAL_DURATION = 500;

    @BindView(R.id.headerContainer)
    protected LinearLayout mHeaderContainer;

    @BindView(R.id.inputContainer)
    protected LinearLayout mInputContainer;

    @BindView(R.id.logo)
    protected ImageView mLogo;

    @BindView(R.id.okay)
    protected ImageView mOkay;

    @BindView(R.id.inputInstanceName)
    protected MaterialEditText mInputInstanceName;

    @BindView(R.id.inputApiHostname)
    protected MaterialEditText mInputApiHostname;

    @BindView(R.id.inputGateway)
    protected MaterialEditText mInputGateway;

    private ArrayList<Boolean> mValidator = new ArrayList<Boolean>(3) {{
        add(false);
        add(false);
        add(false);
    }};

    private ChangedTextWatcher.OnValidateListener mOnValidateListener = new ChangedTextWatcher.OnValidateListener() {
        @Override
        public void onValidated(int index, boolean isValid, boolean hasChanged) {
            mValidator.set(index, isValid);
            ConfigurationFlowActivity.this.validate();
        }

        @Override
        public boolean validate(MaterialEditText editText, Editable s) {
            return ChangedTextWatcher.emptyValidator(editText, s);
        }
    };

    @Override
    protected void onResume() {
        super.onResume();

        mOkay.setColorFilter(getResources().getColor(R.color.colorPrimaryDark), PorterDuff.Mode.SRC_ATOP);

        mInputInstanceName.addTextChangedListener(new ChangedTextWatcher(mInputInstanceName, 0, mOnValidateListener));
        mInputGateway.addTextChangedListener(new ChangedTextWatcher(mInputGateway, 2, mOnValidateListener));
        mInputApiHostname.addTextChangedListener(new ChangedTextWatcher(mInputApiHostname, 1, new ChangedTextWatcher.OnValidateListener() {
            @Override
            public void onValidated(int index, boolean isValid, boolean hasChanged) {
                mValidator.set(index, isValid);
                ConfigurationFlowActivity.this.validate();
            }

            @Override
            public boolean validate(MaterialEditText editText, Editable s) {
                return ChangedTextWatcher.ipPortValidator(editText, s);
            }
        }));
    }

    @OnClick(R.id.okay)
    public void onOkayClicked() {
        if (mOkay.isEnabled()) {
            ConfigurationHandler.getInstance().setup(
                    mInputApiHostname.getText().toString(),
                    mInputInstanceName.getText().toString(),
                    mInputGateway.getText().toString());
            this.finish();
        }
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
                            public void onAnimationStart(Animator animation) {
                            }

                            @Override
                            public void onAnimationEnd(Animator animation) {
                                showKeyboardForView(mInputInstanceName);
                            }

                            @Override
                            public void onAnimationCancel(Animator animation) {
                            }

                            @Override
                            public void onAnimationRepeat(Animator animation) {
                            }
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

    private void validate() {
        boolean notValidated = mValidator.contains(false);
        mOkay.setColorFilter(getResources().getColor(notValidated
                ? R.color.colorPrimaryDark
                : R.color.white), PorterDuff.Mode.SRC_ATOP);
        mOkay.setEnabled(!notValidated);
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
