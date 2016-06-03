package dk.steffenkarlsson.sofa.bdae.view;

import android.content.Context;
import android.support.design.widget.FloatingActionButton;
import android.util.AttributeSet;

import java.util.List;

import butterknife.BindView;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.IActivityHandler;
import dk.steffenkarlsson.sofa.bdae.R;
import dk.steffenkarlsson.sofa.bdae.SubmitJobActivity;
import dk.steffenkarlsson.sofa.bdae.entity.Job;
import dk.steffenkarlsson.sofa.bdae.extra.CustomRequestListener;
import dk.steffenkarlsson.sofa.bdae.extra.TransitionAnimation;
import dk.steffenkarlsson.sofa.bdae.recycler.GenericRecyclerViewModel;
import dk.steffenkarlsson.sofa.bdae.recycler.SubmittedJobRecyclerView;
import dk.steffenkarlsson.sofa.bdae.request.GetSubmittedJobsRequest;
import dk.steffenkarlsson.sofa.networking.Result;

/**
 * Created by steffenkarlsson on 5/31/16.
 */
public class BottomBarDashboardView extends BottomPagerControllerRecyclerView {

    public enum RequestType {
        JOBS
    }

    @BindView(R.id.fab)
    protected FloatingActionButton mAddNewJob;

    public BottomBarDashboardView(Context context) {
        super(context);
    }

    public BottomBarDashboardView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public boolean hasOptionsMenu() {
        return false;
    }

    @Override
    public void setContent(IActivityHandler handler) {
        super.setContent(handler);

        CustomRequestListener listener = new CustomRequestListener(mActivityHandler) {
            @Override
            protected void onData(int id, Result result) {
                List<Job> jobs = (List<Job>) result.response;

                for (Job job : jobs) {
                    mAdapter.add(new GenericRecyclerViewModel(job, SubmittedJobRecyclerView.class));
                }

                mAdapter.notifyDataSetChanged();
            }

            @Override
            public void onError(int id, int statusCode) {
                //TODO: Handle error
            }
        };

        new GetSubmittedJobsRequest()
                .withContext(handler.getActivity())
                .setOnRequestListener(listener)
                .run(RequestType.JOBS);
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.content_dashboard_view;
    }

    @OnClick(R.id.fab)
    public void onFabClicked() {
        mActivityHandler.launchActivity(mActivityHandler.getActivityIntent(
                mActivityHandler.getContext(), SubmitJobActivity.class, false),
                TransitionAnimation.IN_FROM_BOTTOM);
    }
}
