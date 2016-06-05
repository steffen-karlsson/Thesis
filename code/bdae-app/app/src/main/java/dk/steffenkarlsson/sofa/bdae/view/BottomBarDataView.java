package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.util.AttributeSet;

import java.util.List;

import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.extra.DatasetCache;
import dk.steffenkarlsson.sofa.bdae.recycler.DatasetRecyclerView;
import dk.steffenkarlsson.sofa.bdae.recycler.GenericRecyclerViewModel;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarDataView extends BottomPagerControllerRecyclerView {

    public BottomBarDataView(Context context) {
        super(context);
    }

    public BottomBarDataView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public boolean hasOptionsMenu() {
        return false;
    }

    @Override
    public void setContent(IActivityHandler handler) {
        super.setContent(handler);

        DatasetCache.getInstance().getDatasets(mActivityHandler, new DatasetCache.OnDatasetReadyListener() {
            @Override
            public void onReady(List<Dataset> datasets) {
                if (datasets != null) {
                    for (int i = 0; i < datasets.size(); i++) {
                        Dataset dataset = datasets.get(i);
                        dataset.setEven(i % 2 == 0);
                        mAdapter.add(new GenericRecyclerViewModel(dataset, DatasetRecyclerView.class));
                    }
                    mAdapter.notifyDataSetChanged();
                }
            }
        });
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_base_recyclerview;
    }
}
