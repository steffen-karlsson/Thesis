package dk.steffenkarlsson.sofa.bdae.recycler;

import android.content.Context;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.widget.LinearLayout;
import android.widget.TextView;

import butterknife.BindView;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class DatasetRecyclerView extends BaseRecyclerView<Dataset> {

    @BindView(R.id.root)
    protected LinearLayout mRoot;

    @BindView(R.id.name)
    protected TextView mName;

    @BindView(R.id.description)
    protected TextView mDescription;

    @BindView(R.id.jobs)
    protected TextView mJobs;

    public DatasetRecyclerView(Context context) {
        super(context);
    }

    public DatasetRecyclerView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    protected void setTabletContent(Dataset data, boolean isGridLayoutManager) { }

    @Override
    protected void setPhoneContent(Dataset data) {
        mRoot.setBackgroundColor(getResources().getColor(data.isEven()
                ? R.color.colorPrimaryFadedBackground
                : R.color.white));
        mName.setText(data.getName());
        mDescription.setText(data.getDescription());
        if (data.getOperationNames(false).isEmpty())
            mJobs.setText(R.string.job_no_jobs);
        else
            mJobs.setText(TextUtils.join("● ", data.getOperationNames(true)));
    }

    @Override
    protected int getLayoutResource(boolean isTablet, boolean isGridLayoutManager) {
        return R.layout.item_dataset;
    }
}
