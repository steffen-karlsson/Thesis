package dk.steffenkarlsson.sofa.bdae.view;

import android.app.Activity;
import android.content.Context;
import android.support.annotation.IdRes;
import android.support.annotation.MenuRes;
import android.util.AttributeSet;
import android.view.MenuItem;

import dk.steffenkarlsson.sofa.bdae.extra.ViewCache;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public abstract class BasePagerControllerView extends BaseFrameLayout implements ViewCache.ICacheableView {

    protected Activity mActivity;

    public BasePagerControllerView(Context context) {
        super(context);
    }

    public BasePagerControllerView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public abstract boolean hasOptionsMenu();

    public void setContent(Activity activity) {
        this.mActivity = activity;
    }

    public @MenuRes int getOptionsMenuRes() {
        return -1;
    }

    public void onModifyMenuItem(MenuItem menuItem) {
    }

    public void onOptionsMenuClicked(@IdRes int menuId) {
    }
}
