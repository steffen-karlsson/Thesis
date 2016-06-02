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

import butterknife.Bind;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.event.TransitionAnimationEndedEvent;
import dk.steffenkarlsson.sofa.bdae.extra.ConfigurationHandler;

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

    @Bind(R.id.okay)
    protected ImageView mOkay;

    @Bind(R.id.inputInstanceName)
    protected MaterialEditText mInputInstanceName;

    @Bind(R.id.inputApiHostname)
    protected MaterialEditText mInputApiHostname;

    @Bind(R.id.inputGateway)
    protected MaterialEditText mInputGateway;

    private ArrayList<Boolean> mValidator = new ArrayList<Boolean>(3) {{
        add(false);
        add(false);
        add(false);
    }};

    private class EmptyTextWatcher implements TextWatcher {

        private final MaterialEditText mEditText;
        private final int mIndex;

        public EmptyTextWatcher(MaterialEditText editText, int index) {
            this.mEditText = editText;
            this.mIndex = index;
        }

        @Override
        public void beforeTextChanged(CharSequence s, int start, int count, int after) {
        }

        @Override
        public void onTextChanged(CharSequence s, int start, int before, int count) {
        }

        @Override
        public void afterTextChanged(Editable s) {
            boolean isEmpty = TextUtils.isEmpty(s.toString());
            mValidator.add(mIndex, isEmpty);
            if (isEmpty)
                mEditText.setError("Required Field");

            validate();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();

        mOkay.setColorFilter(getResources().getColor(R.color.colorPrimaryDark), PorterDuff.Mode.SRC_ATOP);

        mInputInstanceName.addTextChangedListener(new EmptyTextWatcher(mInputInstanceName, 0));
        mInputGateway.addTextChangedListener(new EmptyTextWatcher(mInputInstanceName, 2));
        mInputApiHostname.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {
            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
            }

            @Override
            public void afterTextChanged(Editable s) {
                boolean validated = false;
                if (TextUtils.isEmpty(s.toString()))
                    mInputApiHostname.setError("Required Field");
                else {
                    if (!isValidIPPort(s.toString()))
                        mInputApiHostname.setError("Has to be a valid ip:port");
                    else
                        validated = true;
                }
                mValidator.add(1, validated);
                validate();
            }
        });
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

    private boolean isValidIPPort(String input) {
        if (!input.contains(":"))
            return false;

        String[] ipport = input.split(":");
        if (ipport.length == 0 || ipport.length == 1)
            return false;

        return Patterns.IP_ADDRESS.matcher(ipport[0]).matches() && TextUtils.isDigitsOnly(ipport[1]);
    }

    private void validate() {
        boolean validated = mValidator.contains(false);
        mOkay.setColorFilter(validated
                ? getResources().getColor(R.color.white)
                : getResources().getColor(R.color.colorPrimaryDark), PorterDuff.Mode.SRC_ATOP);
        mOkay.setEnabled(validated);
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
