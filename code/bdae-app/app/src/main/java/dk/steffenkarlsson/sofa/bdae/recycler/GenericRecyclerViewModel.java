package dk.steffenkarlsson.sofa.bdae.recycler;

import android.view.View;

import dk.steffenkarlsson.sofa.bdae.extra.DeviceUtils;

/**
 * Created by steffenkarlsson on 4/13/16.
 */
public class GenericRecyclerViewModel extends RecyclerAdapter.ViewModel<BaseRecyclerView> {

    private final Object _data;
    private final Class<? extends BaseRecyclerView> _clazz;

    private boolean _isGridLayoutManager;
    private BaseRecyclerView _view;

    public GenericRecyclerViewModel(Object data, Class<? extends BaseRecyclerView> clazz) {
        this._data = data;
        this._clazz = clazz;
    }

    public final void extBind(BaseRecyclerView t, boolean isGridLayoutManager) {
        this._isGridLayoutManager = isGridLayoutManager;
        this.bind(t);
    }

    @Override
    public Class getViewClass() {
        return _clazz;
    }

    @Override
    public void bind(BaseRecyclerView t) {
        boolean isTablet = DeviceUtils.isOnTablet(t.getContext());
        _view = t;
        _view.initialize(isTablet, _isGridLayoutManager);

        if (isTablet)
            _view.setTabletContent(_data, _isGridLayoutManager);
        else
            _view.setPhoneContent(_data);
    }

    public final <T extends BaseRecyclerView> T getView() {
        return (T) this._view;
    }

    public final String getClassName() {
        return this._data.getClass().getName();
    }

    public final <T> T getData() {
        return (T) this._data;
    }

    public void setSelectable(boolean selectable) {
        _view.setSelectable(selectable);
    }

    public void setOnItemClickListener(View.OnClickListener clickListener) {
        _view.setOnItemClickListener(clickListener);
    }
}
