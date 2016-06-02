package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.graphics.PorterDuff;
import android.support.annotation.IdRes;
import android.util.AttributeSet;
import android.view.MenuItem;
import android.view.View;

import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.extra.ViewCache;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarConfigureView extends BasePagerControllerView {

    public BottomBarConfigureView(Context context) {
        super(context);
    }

    public BottomBarConfigureView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    private boolean mConfigurationHasChanged = false;

    @Override
    public boolean hasOptionsMenu() {
        return true;
    }

    @Override
    public void setContent() {

    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_configure_view;
    }

    @Override
    public boolean shouldCache() {
        return true;
    }

    @Override
    public int getOptionsMenuRes() {
        return R.menu.accept;
    }

    @Override
    public void onOptionsMenuClicked(@IdRes int menuId) {
        super.onOptionsMenuClicked(menuId);
    }

    @Override
    public void onModifyMenuItem(MenuItem menuItem) {
        super.onModifyMenuItem(menuItem);

        menuItem.getIcon().setColorFilter(getResources().getColor(mConfigurationHasChanged
                ? R.color.white
                : R.color.colorPrimaryDark), PorterDuff.Mode.SRC_ATOP);
    }

    @Override
    public View getRoot() {
        return this;
    }
}
