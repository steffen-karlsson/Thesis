package dk.steffenkarlsson.sofa.bdae.recycler;

import android.content.Context;
import android.support.annotation.LayoutRes;
import android.support.v7.widget.RecyclerView;
import android.util.AttributeSet;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import butterknife.ButterKnife;

/**
 * Created by steffenkarlsson on 4/13/16.
 */
public abstract class BaseRecyclerView<D> extends FrameLayout {

    private final Context _context;

    public BaseRecyclerView(Context context, AttributeSet attrs) {
        super(context, attrs);
        this._context = context;
    }

    public BaseRecyclerView(Context context) {
        super(context);
        this._context = context;
    }

    public final void initialize(boolean isTablet, boolean isGridLayoutManager) {
        removeAllViewsInLayout();
        setLayoutParams(new RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        inflate(_context, getLayoutResource(isTablet, isGridLayoutManager), this);
        ButterKnife.bind(this);
    }

    protected abstract void setTabletContent(D data, boolean isGridLayoutManager);

    protected abstract void setPhoneContent(D data);

    protected void setSelectable(boolean selectable) {}

    protected abstract @LayoutRes
    int getLayoutResource(boolean isTablet, boolean isGridLayoutManager);

    public void setOnItemClickListener(OnClickListener clickListener) {
        setOnClickListener(clickListener);
    }
}
