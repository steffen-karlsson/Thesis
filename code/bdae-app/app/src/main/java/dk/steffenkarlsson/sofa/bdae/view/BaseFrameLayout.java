package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.support.annotation.LayoutRes;
import android.support.v7.view.ContextThemeWrapper;
import android.util.AttributeSet;
import android.widget.FrameLayout;

import butterknife.ButterKnife;
import dk.steffenkarlsson.sofa.bdae.R;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public abstract class BaseFrameLayout extends FrameLayout {

    public BaseFrameLayout(Context context) {
        super(context);
        init(context);
    }

    public BaseFrameLayout(Context context, AttributeSet attrs) {
        super(context, attrs);
        init(context);
    }

    private void init(Context context) {
        inflate(new ContextThemeWrapper(context, R.style.AppTheme), getLayoutResource(), this);
        ButterKnife.bind(this);
    }

    @LayoutRes
    protected abstract int getLayoutResource();

}