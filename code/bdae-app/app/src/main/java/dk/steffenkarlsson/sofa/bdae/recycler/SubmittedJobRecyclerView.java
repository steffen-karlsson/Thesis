package dk.steffenkarlsson.sofa.bdae.recycler;

import android.content.Context;
import android.graphics.PorterDuff;
import android.text.TextUtils;
import android.util.AttributeSet;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import butterknife.BindView;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.entity.Job;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class SubmittedJobRecyclerView extends BaseRecyclerView<Job> {

    public static interface OnClickListener {
        void onCellClick(String function, String result, String dataType);
        void onArgumentsClick();
    }

    @BindView(R.id.name)
    protected TextView mName;

    @BindView(R.id.identifier)
    protected TextView mIdentifier;

    @BindView(R.id.data_type)
    protected ImageView mDataTypeIcon;

    @BindView(R.id.parameters)
    protected TextView mParameters;

    @BindView(R.id.dataset_name)
    protected TextView mDatasetName;

    @BindView(R.id.status)
    protected TextView mStatus;

    public SubmittedJobRecyclerView(Context context) {
        super(context);
    }

    public SubmittedJobRecyclerView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    protected void setTabletContent(Job data, boolean isGridLayoutManager) { }

    @Override
    protected void setPhoneContent(final Job data) {
        if (data.hasResult() && data.getOnClickListener() != null)
            setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    data.getOnClickListener().onCellClick(data.getName(), data.getResult(), data.getDataType());
                }
            });

        mName.setText(data.getName());
        mIdentifier.setText(data.getIdentifier());
        mDatasetName.setText(data.getDatasetName());
        if (data.getParameters().isEmpty())
            mParameters.setText(R.string.job_no_parameters);
        else {
            mParameters.setText(TextUtils.join(",", data.getParameters()));
            if (data.getOnClickListener() != null)
                mParameters.setOnClickListener(new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        data.getOnClickListener().onArgumentsClick();
                    }
                });
        }

        switch (data.getStatus()) {
            case Done:
                mDataTypeIcon.setVisibility(VISIBLE);
                switch (data.getDataType()) {
                    case "img":
                        mDataTypeIcon.setImageResource(R.drawable.ic_image_white);
                        break;
                    default:
                        mDataTypeIcon.setImageResource(R.drawable.ic_text_white);
                        break;
                }
                mDataTypeIcon.setColorFilter(getResources().getColor(R.color.colorImageTint),
                        PorterDuff.Mode.SRC_ATOP);

                mStatus.setText(getResources().getString(R.string.job_done));
                mStatus.setTextColor(getResources().getColor(R.color.colorDone));
                break;
            case Processing:
                mDataTypeIcon.setVisibility(GONE);
                mStatus.setText(getResources().getString(R.string.job_processing));
                mStatus.setTextColor(getResources().getColor(R.color.colorProcessing));
                break;
        }
    }

    @Override
    protected int getLayoutResource(boolean isTablet, boolean isGridLayoutManager) {
        return R.layout.item_job;
    }
}
