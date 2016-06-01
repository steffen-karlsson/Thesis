package dk.steffenkarlsson.sofa.bdae.extra;

import android.content.Context;
import android.content.res.TypedArray;
import android.util.AttributeSet;
import android.widget.TextView;

import dk.steffenkarlsson.sofa.bdae.R;

/**
 * Created by steffenkarlsson on 6/1/16.
 */
public class RobotoTextView extends TextView {

    private Context mContext;
    private int mFontType;

    public RobotoTextView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init(context, attrs);
    }

    private void init(Context context, AttributeSet attrs) {
        this.mContext = context;

        TypedArray a = context.getTheme().obtainStyledAttributes(attrs, R.styleable.RobotoTextView, 0, 0);
        try {
            this.mFontType = a.getInt(R.styleable.RobotoTextView_fontType, Typefaces.REGULAR);
        } finally {
            a.recycle();
        }

        setFont();
    }

    private void setFont() {
        setTypeface(Typefaces.getInstance().get(mContext, mFontType));
    }

    public void setFontType(int type) {
        this.mFontType = type;
        setFont();
    }
}
