package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.AttributeSet;
import android.view.View;

import java.util.List;

import butterknife.BindView;
import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.extra.CustomRequestListener;
import dk.steffenkarlsson.sofa.bdae.recycler.CustomRecyclerAdapter;
import dk.steffenkarlsson.sofa.bdae.recycler.DatasetRecyclerView;
import dk.steffenkarlsson.sofa.bdae.recycler.GenericRecyclerViewModel;
import dk.steffenkarlsson.sofa.bdae.request.GetDatasetsRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public abstract class BottomPagerControllerRecyclerView extends BasePagerControllerView {

    @BindView(R.id.recyclerView)
    protected RecyclerView mRecyclerView;

    protected CustomRecyclerAdapter mAdapter;

    public BottomPagerControllerRecyclerView(Context context) {
        super(context);
    }

    public BottomPagerControllerRecyclerView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public void setContent(IActivityHandler handler) {
        super.setContent(handler);

        mAdapter = new CustomRecyclerAdapter(getContext(), mRecyclerView);
        mRecyclerView.setLayoutManager(new LinearLayoutManager(getContext()));
        mRecyclerView.setAdapter(mAdapter);
    }

    @Override
    public boolean shouldCache() {
        return true;
    }

    @Override
    public View getRoot() {
        return this;
    }
}
